import json

from ..utils.files import batch_by_chars, select_files
from ..utils.outputs import save_json, save_text
from ..utils.prompts import SYSTEM, render
from ..utils.rating import format_rubric, llm_json, normalize_rating


def _empty_assessment(reason: str) -> dict:
    return {
        "gap_report": {"missing": [], "inaccurate": [], "covered_well": []},
        "code_review": {
            "findings": [],
            "strengths": [],
            "test_gaps": [],
            "scope_note": f"Static review only; assessment fallback used because {reason}.",
        },
        "reproducibility_report": {
            "status": "unknown",
            "prerequisites": [],
            "setup_commands": [],
            "run_commands": [],
            "test_commands": [],
            "configuration": [],
            "verification": [],
            "gaps": ["Repository assessment could not be parsed as valid JSON."],
            "scope_note": "Commands and checks were not executed.",
        },
        "code_understanding": {
            "main_flow": "Unknown",
            "components": [],
            "data_flow": "Unknown",
            "unknowns": ["Repository assessment could not be parsed as valid JSON."],
        },
    }


def _normalize_assessment(assessment: dict) -> dict:
    fallback = _empty_assessment("the model response was incomplete")
    for key, default in fallback.items():
        if not isinstance(assessment.get(key), dict):
            assessment[key] = default
    gap = assessment["gap_report"]
    gap.setdefault("missing", [])
    gap.setdefault("inaccurate", [])
    gap.setdefault("covered_well", [])
    review = assessment["code_review"]
    review.setdefault("findings", [])
    review.setdefault("strengths", [])
    review.setdefault("test_gaps", [])
    review.setdefault("scope_note", "Static review only; no code or tests were executed.")
    repro = assessment["reproducibility_report"]
    repro.setdefault("status", "unknown")
    for key in ["prerequisites", "setup_commands", "run_commands", "test_commands", "configuration", "verification", "gaps"]:
        repro.setdefault(key, [])
    repro.setdefault("scope_note", "Commands and checks were identified from files and were not executed.")
    understanding = assessment["code_understanding"]
    understanding.setdefault("main_flow", "Unknown")
    understanding.setdefault("components", [])
    understanding.setdefault("data_flow", "Unknown")
    understanding.setdefault("unknowns", [])
    return assessment


def make_codebase_analysis(ctx):
    cfg = ctx.settings["github"]

    def codebase_analysis_node(state: dict) -> dict:
        owner, repo, ref = state["owner"], state["repo"], state["default_branch"]

        tree = ctx.gh.get_tree(owner, repo, ref)
        tree_paths = sorted(t["path"] for t in tree)
        tree_text = "\n".join(tree_paths[: cfg["max_tree_lines"]])

        # 1) read a prioritised sample of files
        items = []
        for path in select_files(tree, cfg["max_files"]):
            text = ctx.gh.get_file_text(owner, repo, path, ref)
            if text:
                items.append((path, text[: cfg["max_chars_per_file"]]))

        # 2) map: extract facts per batch (keeps prompts small for free models)
        notes = []
        for batch in batch_by_chars(items, cfg["batch_chars"]):
            files = "\n\n".join(f"### {p}\n{t}" for p, t in batch)
            notes.append(ctx.llm.generate(render("code_map", files=files), system=SYSTEM))

        # 3) reduce: one structured summary
        code_summary = ctx.llm.generate(
            render("code_reduce", tree=tree_text, notes="\n\n".join(notes)), system=SYSTEM
        )

        # 4) assess documentation gaps, code quality, reproducibility, and architecture together
        errors = list(state.get("errors", []))
        try:
            assessment = llm_json(
                ctx.llm,
                render(
                    "repository_assessment",
                    readme=(state["readme_original"] or "(no README)")[:4000],
                    tree=tree_text[:4000],
                    sampled_files="\n".join(path for path, _ in items)[:2000],
                    code_summary=code_summary[:5000],
                ),
            )
        except ValueError as exc:
            errors.append(f"repository assessment fell back to minimal output: {exc}")
            assessment = _empty_assessment(str(exc))
            try:
                assessment["gap_report"] = llm_json(
                    ctx.llm,
                    render("gap_analysis", readme=state["readme_original"] or "(no README)", code_summary=code_summary),
                )
            except Exception as gap_exc:
                errors.append(f"gap analysis also fell back to empty output: {gap_exc}")
        assessment = _normalize_assessment(assessment)
        gap_report = assessment["gap_report"]
        code_review = assessment["code_review"]
        reproducibility_report = assessment["reproducibility_report"]
        code_understanding = assessment["code_understanding"]

        # 5) re-rate using README + gap analysis
        rating_v2 = normalize_rating(
            llm_json(
                ctx.llm,
                render(
                    "readme_rerate",
                    rubric=format_rubric(ctx.rubric),
                    readme=state["readme_original"] or "(no README)",
                    code_summary=code_summary,
                    gap_report=json.dumps(gap_report, indent=2),
                ),
            ),
            ctx.rubric,
        )

        out = state["output_dir"]
        save_text(out, "code_summary.md", code_summary)
        save_json(out, "gap_report.json", gap_report)
        save_json(out, "code_review.json", code_review)
        save_json(out, "reproducibility_report.json", reproducibility_report)
        save_json(out, "code_understanding.json", code_understanding)
        save_json(out, "rating_v2.json", rating_v2)
        return {
            "file_tree": tree_paths,
            "sampled_files": [path for path, _ in items],
            "code_summary": code_summary,
            "gap_report": gap_report,
            "code_review": code_review,
            "reproducibility_report": reproducibility_report,
            "code_understanding": code_understanding,
            "readme_rating_v2": rating_v2,
            "errors": errors,
        }

    return codebase_analysis_node
