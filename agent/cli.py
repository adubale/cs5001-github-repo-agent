import typer
from agent.tools.git_tools import GitTools
from agent.agents.reviewer import ReviewerAgent
from agent.agents.planner import PlannerAgent
from agent.agents.writer import WriterAgent
from agent.agents.critic import CriticAgent

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
    reviewer = ReviewerAgent()
    planner = PlannerAgent()

    diff_text = git_tools.get_diff(base, range_)
    changed_files = git_tools.get_changed_files(base, range_)

    review_result = reviewer.review(diff_text, changed_files)
    plan = planner.plan(review_result)

    typer.echo("[Reviewer] Analysis Complete")

    typer.echo(f"Category: {review_result.category}")
    typer.echo(f"Risk: {review_result.risk}")

    if review_result.findings:
        typer.echo("Findings:")
        for f in review_result.findings:
            typer.echo(f"- {f}")

    typer.echo("Evidence:")
    for e in review_result.evidence:
        typer.echo(f"- {e}")

    typer.echo("\n[Planner] Plan Complete")
    typer.echo(f"Decision: {plan.decision}")
    typer.echo(f"Justification: {plan.justification}")


#    typer.echo("\nChanged files:")
#    if changed_files:
#        for path in changed_files:
#            typer.echo(f"- {path}")
#    else:
#        typer.echo("[No changed files found]")
#    typer.echo("\nDiff Preview:")
#    typer.echo(diff_text if diff_text else "[No diff found]")

@app.command()
def hello():
    typer.echo("CLI is working")

@app.command()
def draft(
        target: str = typer.Argument(..., help="Draft target: issue or pr"),
        instruction: str = typer.Option(None, "--instruction", help="Explicit draft instruction"),
        base: str = typer.Option(None, "--base", help="Base branch to diff against for review-driven drafting"),
        range_: str = typer.Option(None, "--range", help="Range to diff for review driven drafting"),
):
    target = target.lower().strip()
    #print(target)
    #if target not in {"issue, pr"}:
    #    typer.echo("Target must be either 'issue' or 'pr'")
    #    raise typer.Exit(code=1)

    writer = WriterAgent()
    critic = CriticAgent()

    if instruction:
        if base or range:
            typer.echo("Do not combine --instruction with review parameters")
            raise typer.Exit(code=1)

        if target == "issue":
            draft_result = writer.draft_issue_from_instruction(instruction)
        else:
            draft_result = writer.draft_pr_from_instruction(instruction)

        typer.echo("[Writer] Draft created from explicit instruction")
        typer.echo(f"Title: {draft_result.title}")
        typer.echo("Body:")
        typer.echo(draft_result.body)

        reflection = critic.reflect(draft=draft_result)
        typer.echo("\n[Critic] Reflection Complete")
        typer.echo(f"Verdict: {reflection.verdict}")
        if reflection.notes:
            typer.echo("Notes:")
            for note in reflection.notes:
                typer.echo(f"- {note}")
        return

    if (not base and not range_) or (base and range_):
        typer.echo("For review-driven drafting, provide one of either --base or --range")
        raise typer.Exit(code=1)

    git_tools = GitTools()
    reviewer = ReviewerAgent()
    planner = PlannerAgent()

    diff_text = git_tools.get_diff(base, range_)
    changed_files = git_tools.get_changed_files(base, range_)
    review_result = reviewer.review(diff_text, changed_files)
    plan = planner.plan(review_result)

    if target == "issue" and plan.decision != "Create Issue":
        typer.echo(f"[Planner] Decision was '{plan.decision}', not 'Create Issue'")
        raise typer.Exit(code=1)
    if target == "pr" and plan.decision != "Create PR":
        typer.echo(f"[Planner] Decision was '{plan.decision}', not 'Create PR'")
        raise typer.Exit(code=1)

    draft_result = writer.draft_from_review(review_result, plan)
    typer.echo("[Reviewer] Analysis Complete")
    typer.echo(f"Category: {review_result.category}")
    typer.echo(f"Risk: {review_result.risk}")

    if review_result.findings:
        typer.echo("Findings:")
        for f in review_result.findings:
            typer.echo(f"- {f}")

    typer.echo("Evidence:")
    for e in review_result.evidence:
        typer.echo(f"- {e}")

    typer.echo("\n[Planner] Plan Complete")
    typer.echo(f"Decision: {plan.decision}")
    typer.echo(f"Justification: {plan.justification}")

    typer.echo("\n[Writer] Draft Created")
    typer.echo(f"Title: {draft_result.title}")
    typer.echo(f"Body:")
    typer.echo(draft_result.body)

    reflection = critic.reflect(draft=draft_result)
    typer.echo("\n[Critic] Reflection Complete")
    typer.echo(f"Verdict: {reflection.verdict}")
    if reflection.notes:
        typer.echo("Notes:")
        for note in reflection.notes:
            typer.echo(f"- {note}")


if __name__ == "__main__":
    app()