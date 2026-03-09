from agent.models import DraftArtifact
from agent.tools.draft_store import DraftStore
from agent.tools.github_tools import GitHubTools


class GatekeeperAgent:
    def __init__(
        self,
        store: DraftStore | None = None,
        github_tools: GitHubTools | None = None,
    ):
        self.store = store or DraftStore()
        self.github_tools = github_tools

    def approve(
        self,
        draft_id: str,
        yes: bool,
        pr_head: str | None = None,
        pr_base: str | None = None,
    ) -> DraftArtifact:
        artifact = self.store.get(draft_id)
        self._ensure_actionable(artifact)

        if not yes:
            artifact.status = "rejected"
            self.store.update(artifact)
            return artifact

        artifact.status = "approved"
        self.store.update(artifact)

        if self.github_tools is None:
            return artifact

        created = self._create_on_github(
            artifact=artifact,
            pr_head=pr_head,
            pr_base=pr_base,
        )

        self.store.update(created)
        return created

    @staticmethod
    def _ensure_actionable(artifact: DraftArtifact) -> None:
        if artifact.status not in {"drafted", "approved"}:
            raise ValueError(
                f"Draft {artifact.id} is in status {artifact.status!r} and cannot be approved."
            )

        if artifact.reflection_result is None:
            raise ValueError(f"Draft {artifact.id} has no reflection result.")

        if artifact.reflection_result.verdict.upper() != "PASS":
            raise ValueError(
                f"Draft {artifact.id} cannot be approved because critic verdict is "
                f"{artifact.reflection_result.verdict!r}."
            )

    def _create_on_github(
        self,
        artifact: DraftArtifact,
        pr_head: str | None,
        pr_base: str | None,
    ) -> DraftArtifact:
        if artifact.kind == "issue":
            result = self.github_tools.create_issue(
                title=artifact.title,
                body=artifact.body,
            )

        elif artifact.kind == "pr":
            if not pr_head or not pr_base:
                raise ValueError("PR creation requires both --head and --base.")

            result = self.github_tools.create_pr(
                title=artifact.title,
                body=artifact.body,
                head=pr_head,
                base=pr_base,
            )

        else:
            raise ValueError(f"Unsupported draft kind: {artifact.kind!r}")

        artifact.status = "created"
        artifact.github_number = result["number"]
        artifact.github_url = result["url"]
        artifact.github_error = None

        return artifact