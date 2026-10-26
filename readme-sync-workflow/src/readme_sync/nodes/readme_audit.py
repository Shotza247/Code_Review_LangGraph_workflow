from ..github.url import parse_repo_url
from ..utils.outputs import output_dir, save_json, save_text
from ..utils.prompts import render
from ..utils.rating import format_rubric, llm_json, normalize_rating


def make_readme_audit(ctx):
    def readme_audit_node(state: dict) -> dict:
        ref = parse_repo_url(state["repo_url"])
        info = ctx.gh.get_repo(ref.owner, ref.repo)
        branch = info["default_branch"]
        path, readme = ctx.gh.get_readme(ref.owner, ref.repo, branch)

        prompt = render(
            "readme_audit",
            rubric=format_rubric(ctx.rubric),
            readme=readme or "(this repository has no README)",
        )
        rating = normalize_rating(llm_json(ctx.llm, prompt), ctx.rubric)

        out = output_dir(ctx.settings, ref.owner, ref.repo)
        save_text(out, "README.original.md", readme)
        save_json(out, "audit.json", rating)
        return {
            "owner": ref.owner,
            "repo": ref.repo,
            "default_branch": branch,
            "readme_path": path,
            "readme_original": readme,
            "readme_rating_v1": rating,
            "output_dir": str(out),
        }

    return readme_audit_node
