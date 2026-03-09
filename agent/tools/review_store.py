import json
from pathlib import Path
from uuid import uuid4

from agent.models import ReviewArtifact


class ReviewStore:
    def __init__(self, root: str = ".agent/reviews"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return f"review-{uuid4().hex[:8]}"

    def _path_for(self, review_id: str) -> Path:
        return self.root / f"{review_id}.json"

    def save(self, artifact: ReviewArtifact) -> None:
        path = self._path_for(artifact.id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f, indent=2)

    def get(self, review_id: str) -> ReviewArtifact:
        path = self._path_for(review_id)
        if not path.exists():
            raise FileNotFoundError(f"No review found with id {review_id}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return ReviewArtifact.from_dict(data)

    def list_all(self) -> list[ReviewArtifact]:
        artifacts = []
        for path in self.root.glob("*.json"):
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            artifacts.append(ReviewArtifact.from_dict(data))
        return artifacts