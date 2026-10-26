import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str


_PATTERN = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$"
)


def parse_repo_url(url: str) -> RepoRef:
    m = _PATTERN.match(url.strip())
    if not m:
        raise ValueError(f"Not a valid GitHub repo URL: {url!r}")
    return RepoRef(owner=m.group(1), repo=m.group(2))
