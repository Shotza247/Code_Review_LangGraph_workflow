import re
from pathlib import Path

from ..utils.mermaid import validate_mermaid
from ..utils.outputs import save_json, save_text
from ..utils.prompts import SYSTEM, render

START, END = "<!-- DIAGRAMS:START -->", "<!-- DIAGRAMS:END -->"
KEYWORDS = ("flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram", "journey", "gantt")
UNVALIDATED_WARNING = "diagrams were only structurally checked (mmdc not used): {why}"


def _extract_mermaid(text: str) -> str | None:
    m = re.search(r"```mermaid\s*(.*?)```", text, re.S)
    code = (m.group(1) if m else text).strip()
    first = next((ln for ln in code.splitlines() if ln.strip()), "")
    return code if first.strip().startswith(KEYWORDS) and "```" not in code else None


def splice_diagrams(readme: str, blocks: list[tuple[str, str]]) -> str:
    body = "\n\n".join(f"### {title}\n\n```mermaid\n{code}\n```" for title, code in blocks)
    block = f"{START}\n{body}\n{END}"
    if START in readme and END in readme:
        return re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _m: block, readme, flags=re.S)
    return readme.rstrip() + f"\n\n## Architecture and flows\n\n{block}\n"


def make_diagrams(ctx):
    specs = ctx.settings["diagrams"]
    max_lines = ctx.settings["github"]["max_tree_lines"]
    vcfg = ctx.settings.get("mermaid_validation", {})
    max_repairs = vcfg.get("max_repairs", 2)

    def build_one(spec: dict, tree: str, state: dict, svg_path: Path):
        """Returns (code | None, svg | None, skip_reason | None, unvalidated_note | None)."""
        prompt = render(
            "diagram",
            diagram_name=spec["name"],
            diagram_type=spec["type"],
            description=spec["description"],
            tree=tree,
            code_summary=state["code_summary"],
        )
        code = None
        for _ in range(2):  # one retry if the output does not look like Mermaid at all
            code = _extract_mermaid(ctx.llm.generate(prompt, system=SYSTEM))
            if code:
                break
        if not code:
            return None, None, "model did not return Mermaid", None

        for attempt in range(max_repairs + 1):
            result = validate_mermaid(code, svg_path, vcfg)
            if result.ok:
                return code, result.svg_path, None, (None if result.validated else result.note)
            if attempt == max_repairs:
                return None, None, f"still invalid after {max_repairs} repairs: {result.error[:160]}", None
            repair = render(
                "diagram_repair", diagram_type=spec["type"], code=code, error=result.error
            )
            fixed = _extract_mermaid(ctx.llm.generate(repair, system=SYSTEM))
            if fixed:
                code = fixed
        return None, None, "validation loop ended unexpectedly", None

    def diagrams_node(state: dict) -> dict:
        tree = "\n".join(state["file_tree"][:max_lines])
        out = state["output_dir"]
        diagrams, svgs, blocks = {}, {}, []
        errors = list(state.get("errors", []))
        unvalidated_notes: set[str] = set()

        for spec in specs:
            svg_path = Path(out) / "diagrams" / f"{spec['name']}.svg"
            code, svg, skip, note = build_one(spec, tree, state, svg_path)
            if code:
                diagrams[spec["name"]] = code
                blocks.append((spec["title"], code))
                save_text(out, f"diagrams/{spec['name']}.mmd", code)
                if svg:
                    svgs[spec["name"]] = svg
                if note:
                    unvalidated_notes.add(note)
            else:
                errors.append(f"diagram '{spec['name']}' skipped: {skip}")

        for note in sorted(unvalidated_notes):
            errors.append(UNVALIDATED_WARNING.format(why=note))

        readme = splice_diagrams(state["readme_synced"], blocks) if blocks else state["readme_synced"]
        save_text(out, "README.new.md", readme)
        save_json(
            out,
            "run_summary.json",
            {
                "repo": f"{state['owner']}/{state['repo']}",
                "rating_before": state["readme_rating_v1"]["score"],
                "rating_after_analysis": state["readme_rating_v2"]["score"],
                "sampled_files": len(state.get("sampled_files", [])),
                "code_review_findings": len(state.get("code_review", {}).get("findings", [])),
                "reproducibility_status": state.get("reproducibility_report", {}).get("status", "unknown"),
                "diagrams": list(diagrams),
                "diagrams_rendered_with_mmdc": list(svgs),
                "errors": errors,
            },
        )
        return {"readme_synced": readme, "diagrams": diagrams, "diagram_svgs": svgs, "errors": errors}

    return diagrams_node
