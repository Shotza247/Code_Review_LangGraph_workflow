from ..config import pr_mode
from ..utils.outputs import save_json


def make_open_pr(ctx):
    cfg = ctx.settings["pr"]

    def open_pr_node(state: dict) -> dict:
        mode = pr_mode(ctx.settings)
        errors = list(state.get("errors", []))
        if not getattr(ctx.gh, "token", None):
            errors.append("PR skipped: GITHUB_TOKEN is not set")
            return {"errors": errors}

        owner, repo, base = state["owner"], state["repo"], state["default_branch"]
        sha = ctx.gh.get_branch_sha(owner, repo, base)

        target_owner = ctx.gh.fork_repo(owner, repo) if mode == "fork" else owner
        branch = cfg["branch_name"]
        ctx.gh.create_branch(target_owner, repo, branch, sha)

        files = {state["readme_path"]: state["readme_synced"]}
        if cfg.get("include_course_plan"):
            files[cfg["course_plan_path"]] = state["course_plan"]
        for path, text in files.items():
            ctx.gh.put_file(target_owner, repo, path, text, cfg["commit_message"], branch)

        head = branch if mode == "direct" else f"{target_owner}:{branch}"
        body = (
            "Automated README update from readme-sync-workflow.\n\n"
            f"- Reproducibility rating before: **{state['readme_rating_v1']['score']}/100**\n"
            f"- Rating after gap analysis: **{state['readme_rating_v2']['score']}/100**\n"
            f"- Gaps found: {len(state['gap_report'].get('missing', []))} missing, "
            f"{len(state['gap_report'].get('inaccurate', []))} inaccurate\n\n"
            "Please review generated commands before merging."
        )
        url = ctx.gh.open_pull_request(owner, repo, cfg["title"], body, head, base)
        save_json(state["output_dir"], "pr.json", {"url": url, "mode": mode})
        return {"pr_url": url, "errors": errors}

    return open_pr_node
