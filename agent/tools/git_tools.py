import subprocess

class GitTools:
    @staticmethod
    def run(args: list[str]) -> str:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def get_diff_against_base(self, base: str) -> str:
        return self.run(["git", "diff", f"{base}...HEAD"])

    def get_changed_files_against_base(self, base: str) -> list[str]:
        output = self.run(["git", "diff", "--name-only", f"{base}...HEAD"])
        return [line for line in output.splitlines() if line.strip()]