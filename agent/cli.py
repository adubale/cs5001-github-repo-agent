import typer
from dotenv import load_dotenv

load_dotenv()

from agent.tools.git_tools import GitTools
from agent.tools.github_tools import GitHubTools

from agent.agents.reviewer import ReviewerAgent
from agent.agents.planner import PlannerAgent
from agent.agents.writer import WriterAgent
from agent.agents.critic import CriticAgent
from agent.agents.gatekeeper import GatekeeperAgent
from agent.agents.improver import ImproverAgent

from agent.tools.draft_store import DraftStore
from agent.tools.review_store import ReviewStore

from agent.models import DraftArtifact, ReviewArtifact


app = typer.Typer(help="Personalized GitHub Repo Agent")


@app.command()
def review(
    base: str = typer.Option(None, "--base", help="Base branch to diff against"),
    range_: str = typer.Option(None, "--range", help="Range to diff"),
):
    if (not base and not range_) or (base and range_):
        typer.echo("Please provide one of either --base or --range")
        raise typer.Exit(code=1)

    git_tools = GitTools()
    reviewer = ReviewerAgent()
    planner = PlannerAgent()
    store = ReviewStore()

    diff_text = git_tools.get_diff(base, range_)
    changed_files = git_tools.get_changed_files(base, range_)

    review_result = reviewer.review(diff_text, changed_files)
    plan = planner.plan(review_result)

    artifact = ReviewArtifact(
        id=store.new_id(),
        category=review_result.category,
        risk=review_result.risk,
        findings=review_result.findings,
        evidence=review_result.evidence,
        plan_result=plan,
    )

    store.save(artifact)

    typer.echo("[Reviewer] Analysis Complete")
    typer.echo(f"Review ID: {artifact.id}")
    typer.echo(f"Category: {artifact.category}")
    typer.echo(f"Risk: {artifact.risk}")

    if artifact.findings:
        typer.echo("Findings:")
        for f in artifact.findings:
            typer.echo(f"- {f}")

    typer.echo("Evidence:")
    for e in artifact.evidence:
        typer.echo(f"- {e}")

    typer.echo("\n[Planner] Plan Complete")
    typer.echo(f"Decision: {artifact.plan_result.decision}")
    typer.echo(f"Justification: {artifact.plan_result.justification}")


@app.command()
def draft(
    target: str = typer.Argument(...),
    instruction: str = typer.Option(None, "--instruction"),
    base: str = typer.Option(None, "--base"),
    range_: str = typer.Option(None, "--range"),
):
    target = target.lower().strip()

    if target not in {"issue", "pr"}:
        typer.echo("Target must be either 'issue' or 'pr'")
        raise typer.Exit(code=1)

    writer = WriterAgent()
    critic = CriticAgent()
    store = DraftStore()

    if instruction:
        if target == "issue":
            draft_result = writer.draft_issue_from_instruction(instruction)
        else:
            draft_result = writer.draft_pr_from_instruction(instruction)

        reflection = critic.reflect_from_instruction(
            draft=draft_result,
            instruction=instruction,
            target=target,
        )

        artifact = DraftArtifact(
            id=store.new_id(),
            kind=target,
            source="instruction",
            title=draft_result.title,
            body=draft_result.body,
            status="drafted",
            review_result=None,
            plan_result=None,
            reflection_result=reflection,
        )

        store.save(artifact)

        typer.echo(f"Draft ID: {artifact.id}")
        typer.echo(artifact.title)
        typer.echo(artifact.body)

        typer.echo("\n[Critic] Reflection Complete")
        typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
        if artifact.reflection_result.notes:
            typer.echo("Notes:")
            for note in artifact.reflection_result.notes:
                typer.echo(f"- {note}")
        return

    if (not base and not range_) or (base and range_):
        typer.echo("Provide one of --base or --range")
        raise typer.Exit(code=1)

    git_tools = GitTools()
    reviewer = ReviewerAgent()
    planner = PlannerAgent()

    diff_text = git_tools.get_diff(base, range_)
    changed_files = git_tools.get_changed_files(base, range_)

    review_result = reviewer.review(diff_text, changed_files)
    plan = planner.plan(review_result)

    draft_result = writer.draft_from_review(review_result, plan)

    reflection = critic.reflect_from_review(
        draft=draft_result,
        review=review_result,
        plan=plan,
    )

    artifact = DraftArtifact(
        id=store.new_id(),
        kind=target,
        source="review",
        title=draft_result.title,
        body=draft_result.body,
        status="drafted",
        review_result=review_result,
        plan_result=plan,
        reflection_result=reflection,
    )

    store.save(artifact)

    typer.echo(f"Draft ID: {artifact.id}")
    typer.echo(artifact.title)
    typer.echo(artifact.body)

    typer.echo("\n[Critic] Reflection Complete")
    typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
    if artifact.reflection_result.notes:
        typer.echo("Notes:")
        for note in artifact.reflection_result.notes:
            typer.echo(f"- {note}")


@app.command()
def improve(
    target: str = typer.Argument(...),
    number: int = typer.Option(..., "--number"),
    repo: str = typer.Option(None, "--repo"),
):
    target = target.lower().strip()

    if target not in {"issue", "pr"}:
        typer.echo("Target must be either 'issue' or 'pr'")
        raise typer.Exit(code=1)

    github_tools = GitHubTools(repo=repo)
    improver = ImproverAgent()

    if target == "issue":
        artifact = github_tools.get_issue(number)
        result = improver.improve_issue(
            title=artifact.get("title", ""),
            body=artifact.get("body", ""),
        )
    else:
        artifact = github_tools.get_pr(number)
        result = improver.improve_pr(
            title=artifact.get("title", ""),
            body=artifact.get("body", ""),
        )

    typer.echo("[Reviewer] Critique")
    for item in result["critique"]:
        typer.echo(f"- {item}")

    typer.echo("\n[Reviewer] Suggested Acceptance Criteria")
    if result["suggested_acceptance_criteria"]:
        for item in result["suggested_acceptance_criteria"]:
            typer.echo(f"- {item}")
    else:
        typer.echo("- None provided")

    typer.echo("\n[Writer] Proposed Improved Version")
    typer.echo(result["improved_title"])
    typer.echo(result["improved_body"])


@app.command()
def drafts():
    store = DraftStore()

    for artifact in store.list_all():
        verdict = "N/A"
        if artifact.reflection_result:
            verdict = artifact.reflection_result.verdict

        typer.echo(
            f"{artifact.id} | {artifact.kind} | {artifact.status} | {verdict} | {artifact.title}"
        )


@app.command()
def show_draft(draft_id: str):
    store = DraftStore()
    artifact = store.get(draft_id)

    typer.echo(artifact.id)
    typer.echo(artifact.title)
    typer.echo(artifact.body)

    if artifact.reflection_result:
        typer.echo("\n[Critic] Reflection")
        typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
        if artifact.reflection_result.notes:
            typer.echo("Notes:")
            for note in artifact.reflection_result.notes:
                typer.echo(f"- {note}")


@app.command()
def approve(
    draft_id: str = typer.Option(..., "--id"),
    yes: bool = typer.Option(False, "--yes"),
    no: bool = typer.Option(False, "--no"),
    repo: str = typer.Option(None, "--repo"),
    head: str = typer.Option(None, "--head"),
    base: str = typer.Option(None, "--base"),
):
    if yes == no:
        typer.echo("Provide exactly one of --yes or --no")
        raise typer.Exit(code=1)

    store = DraftStore()

    if no:
        gatekeeper = GatekeeperAgent(store=store)
        updated = gatekeeper.approve(draft_id=draft_id, yes=False)
        typer.echo(f"Status: {updated.status}")
        return

    github_tools = GitHubTools(repo=repo)
    gatekeeper = GatekeeperAgent(store=store, github_tools=github_tools)

    updated = gatekeeper.approve(
        draft_id=draft_id,
        yes=True,
        pr_head=head,
        pr_base=base,
    )

    typer.echo(f"Status: {updated.status}")

    if getattr(updated, "github_url", None):
        typer.echo(updated.github_url)


if __name__ == "__main__":
    app()