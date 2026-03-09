import json
from pathlib import Path
from uuid import uuid4

from agent.models import DraftArtifact


class DraftStore:
    def __init__(self, root: str = ".agent/drafts"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def new_id() -> str:
        return f"draft-{uuid4().hex[:8]}"

    def _path_for(self, draft_id: str) -> Path:
        return self.root / f"{draft_id}.json"

    def save(self, artifact: DraftArtifact) -> None:
        path = self._path_for(artifact.id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def get(self, draft_id: str) -> DraftArtifact:
        path = self._path_for(draft_id)
        if not path.exists():
            raise FileNotFoundError(f"No draft found with id {draft_id}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return DraftArtifact.from_dict(data)

    def update(self, artifact: DraftArtifact) -> None:
        self.save(artifact)

    def list_all(self) -> list[DraftArtifact]:
        artifacts = []
        for path in self.root.glob("*.json"):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            artifacts.append(DraftArtifact.from_dict(data))
        return artifacts