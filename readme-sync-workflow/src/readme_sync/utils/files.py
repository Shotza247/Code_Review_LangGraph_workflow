import re
from pathlib import PurePosixPath

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".idea",
             ".vscode", "vendor", "target", ".next", "site-packages", "coverage"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip", ".gz", ".tar", ".mp4",
            ".mp3", ".woff", ".woff2", ".ttf", ".eot", ".pyc", ".so", ".dll", ".exe", ".bin",
            ".parquet", ".csv", ".ipynb", ".lock", ".min.js", ".map"}
SKIP_NAMES = {"package-lock.json", "yarn.lock", "poetry.lock", "pnpm-lock.yaml", "readme.md"}
MANIFESTS = {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "package.json", "pom.xml",
             "build.gradle", "go.mod", "cargo.toml", "gemfile", "composer.json", "pipfile",
             "environment.yml", "dockerfile", "docker-compose.yml", "docker-compose.yaml",
             "makefile", ".env.example", "env.example"}
ENTRY = re.compile(r"(^|/)(main|app|index|server|cli|run|manage|__main__|wsgi|asgi)\.[a-z]+$")


def _score(path: str) -> int:
    p = PurePosixPath(path)
    name = p.name.lower()
    s = 0
    if name in MANIFESTS:
        s += 100
    if ENTRY.search(path.lower()):
        s += 80
    if p.suffix.lower() in {".yaml", ".yml", ".toml", ".json", ".ini", ".cfg"} or ".github/workflows" in path:
        s += 40
    if p.suffix.lower() in {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".php", ".sh"}:
        s += 30
    if "test" in path.lower():
        s -= 20
    if p.suffix.lower() == ".md":
        s -= 10
    return s - 3 * len(p.parts)  # prefer shallow files


def select_files(tree: list[dict], max_files: int) -> list[str]:
    candidates = []
    for t in tree:
        path, size = t["path"], t.get("size", 0)
        parts = PurePosixPath(path).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        low = path.lower()
        if PurePosixPath(path).name.lower() in SKIP_NAMES or any(low.endswith(e) for e in SKIP_EXT):
            continue
        if size > 200_000:
            continue
        candidates.append(path)
    return sorted(candidates, key=_score, reverse=True)[:max_files]


def batch_by_chars(items: list[tuple[str, str]], budget: int) -> list[list[tuple[str, str]]]:
    batches, cur, used = [], [], 0
    for path, text in items:
        cost = len(text) + len(path) + 20
        if cur and used + cost > budget:
            batches.append(cur)
            cur, used = [], 0
        cur.append((path, text))
        used += cost
    if cur:
        batches.append(cur)
    return batches
