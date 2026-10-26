import base64
import os
import time

import requests

API = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    """Thin REST wrapper. Reads work without a token (rate-limited); PR mode needs one."""

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.s = requests.Session()
        self.s.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "readme-sync-workflow"})
        if self.token:
            self.s.headers["Authorization"] = f"Bearer {self.token}"

    # -- low level -----------------------------------------------------------
    def _req(self, method: str, path: str, ok=(200, 201), **kw):
        r = self.s.request(method, f"{API}{path}", timeout=30, **kw)
        if r.status_code == 403 and "rate limit" in r.text.lower():
            raise GitHubError("GitHub rate limit hit. Set GITHUB_TOKEN to raise the limit.")
        if r.status_code not in ok:
            raise GitHubError(f"{method} {path} -> {r.status_code}: {r.text[:300]}")
        return r

    # -- reads ---------------------------------------------------------------
    def get_repo(self, owner: str, repo: str) -> dict:
        return self._req("GET", f"/repos/{owner}/{repo}").json()

    def get_readme(self, owner: str, repo: str, ref: str) -> tuple[str, str]:
        r = self._req("GET", f"/repos/{owner}/{repo}/readme", ok=(200, 404), params={"ref": ref})
        if r.status_code == 404:
            return "README.md", ""
        data = r.json()
        return data["path"], base64.b64decode(data["content"]).decode("utf-8", errors="replace")

    def get_tree(self, owner: str, repo: str, ref: str) -> list[dict]:
        data = self._req("GET", f"/repos/{owner}/{repo}/git/trees/{ref}", params={"recursive": "1"}).json()
        return [{"path": t["path"], "size": t.get("size", 0)} for t in data["tree"] if t["type"] == "blob"]

    def get_file_text(self, owner: str, repo: str, path: str, ref: str) -> str | None:
        r = self._req("GET", f"/repos/{owner}/{repo}/contents/{path}", ok=(200, 404), params={"ref": ref})
        if r.status_code == 404:
            return None
        data = r.json()
        if not isinstance(data, dict) or "content" not in data or not data["content"]:
            return None  # directory or >1MB file
        try:
            return base64.b64decode(data["content"]).decode("utf-8")
        except UnicodeDecodeError:
            return None  # binary

    # -- writes (PR mode) ----------------------------------------------------
    def get_user(self) -> str:
        return self._req("GET", "/user").json()["login"]

    def get_branch_sha(self, owner: str, repo: str, branch: str) -> str:
        return self._req("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}").json()["object"]["sha"]

    def fork_repo(self, owner: str, repo: str) -> str:
        """Fork into the authenticated user's account; returns the fork owner login."""
        fork_owner = self.get_user()
        self._req("POST", f"/repos/{owner}/{repo}/forks", ok=(200, 201, 202), json={})
        for _ in range(15):  # forks are created asynchronously
            r = self.s.get(f"{API}/repos/{fork_owner}/{repo}", timeout=30)
            if r.status_code == 200:
                return fork_owner
            time.sleep(2)
        raise GitHubError("Fork did not become available in time.")

    def create_branch(self, owner: str, repo: str, name: str, sha: str) -> None:
        r = self.s.post(
            f"{API}/repos/{owner}/{repo}/git/refs", json={"ref": f"refs/heads/{name}", "sha": sha}, timeout=30
        )
        if r.status_code == 422 and "already exists" in r.text:
            return  # reuse the branch
        if r.status_code not in (200, 201):
            raise GitHubError(f"create_branch -> {r.status_code}: {r.text[:300]}")

    def put_file(self, owner: str, repo: str, path: str, text: str, message: str, branch: str) -> None:
        existing = self._req(
            "GET", f"/repos/{owner}/{repo}/contents/{path}", ok=(200, 404), params={"ref": branch}
        )
        body = {
            "message": message,
            "content": base64.b64encode(text.encode()).decode(),
            "branch": branch,
        }
        if existing.status_code == 200:
            body["sha"] = existing.json()["sha"]
        self._req("PUT", f"/repos/{owner}/{repo}/contents/{path}", json=body)

    def open_pull_request(self, base_owner: str, repo: str, title: str, body: str, head: str, base: str) -> str:
        r = self._req(
            "POST",
            f"/repos/{base_owner}/{repo}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        return r.json()["html_url"]
