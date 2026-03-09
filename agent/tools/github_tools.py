import os
import requests


class GitHubTools:
    def __init__(self, repo: str | None = None, token: str | None = None):
        self.repo = repo or os.getenv("GITHUB_REPOSITORY")
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.repo:
            raise ValueError("GitHub repository not configured. Set GITHUB_REPOSITORY=owner/repo")
        if not self.token:
            raise ValueError("GitHub token not configured. Set GITHUB_TOKEN")

        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue(self, title: str, body: str) -> dict:
        response = requests.post(
            f"{self.base_url}/issues",
            headers=self.headers,
            json={"title": title, "body": body},
            timeout=30,
        )
        self._raise_for_status(response, "create issue")
        data = response.json()
        return {
            "number": data["number"],
            "url": data["html_url"],
        }

    def create_pr(
        self,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> dict:
        response = requests.post(
            f"{self.base_url}/pulls",
            headers=self.headers,
            json={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
            },
            timeout=30,
        )
        self._raise_for_status(response, "create pull request")
        data = response.json()
        return {
            "number": data["number"],
            "url": data["html_url"],
        }

    def get_issue(self, number: int) -> dict:
        response = requests.get(
            f"{self.base_url}/issues/{number}",
            headers=self.headers,
            timeout=30,
        )
        self._raise_for_status(response, "get issue")
        return response.json()

    def get_pr(self, number: int) -> dict:
        response = requests.get(
            f"{self.base_url}/pulls/{number}",
            headers=self.headers,
            timeout=30,
        )
        self._raise_for_status(response, "get pull request")
        return response.json()

    @staticmethod
    def _raise_for_status(response: requests.Response, action: str) -> None:
        if response.ok:
            return

        try:
            payload = response.json()
            message = payload.get("message", response.text)
        except Exception:
            message = response.text

        raise RuntimeError(f"GitHub API failed to {action}: {response.status_code} {message}")