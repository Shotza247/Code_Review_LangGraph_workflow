from typing import Any, TypedDict


class RepoState(TypedDict, total=False):
    """Shared state passed between nodes (same idea as PipelineState in the PDF)."""

    # input
    repo_url: str

    # node 1: readme_audit
    owner: str
    repo: str
    default_branch: str
    readme_path: str
    readme_original: str
    readme_rating_v1: dict[str, Any]
    output_dir: str

    # node 2: codebase_analysis
    file_tree: list[str]
    sampled_files: list[str]
    code_summary: str
    gap_report: dict[str, Any]
    code_review: dict[str, Any]
    reproducibility_report: dict[str, Any]
    code_understanding: dict[str, Any]
    readme_rating_v2: dict[str, Any]

    # node 3: course_plan
    course_plan: str

    # node 4: readme_sync
    readme_synced: str

    # node 5: diagrams
    diagrams: dict[str, str]
    diagram_svgs: dict[str, str]  # only when mmdc rendered them

    # node 6 (optional): open_pr
    pr_url: str

    errors: list[str]
    audit_log: list[dict[str, Any]]
