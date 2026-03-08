import typer
from agent.tools.git_tools import GitTools

app = typer.Typer(help="Personalized GitHub Repo Agent")

@app.command()
def review(base: str = typer.Option(..., "--base", help="Base branch to diff against")):
    git_tools = GitTools()

    diff_text = git_tools.get_diff_against_base(base)
    changed_files = git_tools.get_changed_files_against_base(base)

    typer.echo(f"Reviewing against base branch: {base}")

    typer.echo("\nChanged files:")
    if changed_files:
        for path in changed_files:
            typer.echo(f"- {path}")
    else:
        typer.echo("[No changed files found]")

    typer.echo("\nDiff Preview:")
    typer.echo(diff_text if diff_text else "[No diff found]")


@app.command()
def hello():
    typer.echo("CLI is working")

if __name__ == "__main__":
    app()