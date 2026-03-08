import subprocess

class GitTools:
    @staticmethod
    def run(args: list[str]) -> str:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    @staticmethod
    def _build_diff_target(base: str | None = None, commit_range: str | None = None) -> str:
        if base:
            return f"{base}"
        return commit_range

    def get_diff(self, base, commit_range) -> str:
        target = self._build_diff_target(base=base, commit_range=commit_range)
        return self.run(["git", "diff", target])

    def get_changed_files(self, base, commit_range) -> list[str]:
        target = self._build_diff_target(base=base, commit_range=commit_range)
        output = self.run(["git", "diff", "--name-only", target])
        return [line for line in output.splitlines() if line.strip()]