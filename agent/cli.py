import typer
from agent.tools.git_tools import GitTools

app = typer.Typer(help="Personalized GitHub Repo Agent")

@app.command()
def review(
        #options
        base: str = typer.Option(None, "--base", help="Base branch to diff against"),
        range_: str = typer.Option(None, "--range", help="Range to diff"),
):
    if (not base and not range_) or (base and range_):
        typer.echo("Please provide one of either --base or --range")
        raise typer.Exit(code=1)

    git_tools = GitTools()

    diff_text = git_tools.get_diff(base, range_)
    changed_files = git_tools.get_changed_files(base, range_)

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