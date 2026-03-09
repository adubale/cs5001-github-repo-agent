import typer
from agent.tools.git_tools import GitTools
from agent.agents.reviewer import ReviewerAgent
from agent.agents.planner import PlannerAgent
from agent.agents.writer import WriterAgent
from agent.agents.critic import CriticAgent
from agent.tools.draft_store import DraftStore
from agent.tools.review_store import ReviewStore
from agent.models import DraftArtifact, ReviewArtifact

app = typer.Typer(help="Personalized GitHub Repo Agent")


@app.command()
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

    if target not in {"issue", "pr"}:
        typer.echo("Target must be either 'issue' or 'pr'")
        raise typer.Exit(code=1)

    writer = WriterAgent()
    critic = CriticAgent()
    store = DraftStore()

    if instruction:
        if base or range_:
            typer.echo("Do not combine --instruction with review parameters")
            raise typer.Exit(code=1)

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

        typer.echo("[Writer] Draft created from explicit instruction")
        typer.echo(f"Draft ID: {artifact.id}")
        typer.echo(f"Title: {artifact.title}")
        typer.echo("Body:")
        typer.echo(artifact.body)

        typer.echo("\n[Critic] Reflection Complete")
        typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
        if artifact.reflection_result.notes:
            typer.echo("Notes:")
            for note in artifact.reflection_result.notes:
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
    typer.echo(f"Draft ID: {artifact.id}")
    typer.echo(f"Title: {artifact.title}")
    typer.echo("Body:")
    typer.echo(artifact.body)

    typer.echo("\n[Critic] Reflection Complete")
    typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
    if artifact.reflection_result.notes:
        typer.echo("Notes:")
        for note in artifact.reflection_result.notes:
            typer.echo(f"- {note}")


@app.command()
def drafts():
    store = DraftStore()
    artifacts = store.list_all()

    if not artifacts:
        typer.echo("No drafts found.")
        return

    for artifact in artifacts:
        verdict = "N/A"
        if artifact.reflection_result:
            verdict = artifact.reflection_result.verdict

        typer.echo(
            f"{artifact.id} | {artifact.kind} | {artifact.source} | "
            f"{artifact.status} | {verdict} | {artifact.title}"
        )


@app.command()
def show_draft(
    draft_id: str = typer.Argument(..., help="Draft artifact ID"),
):
    store = DraftStore()

    try:
        artifact = store.get(draft_id)
    except FileNotFoundError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    typer.echo(f"ID: {artifact.id}")
    typer.echo(f"Kind: {artifact.kind}")
    typer.echo(f"Source: {artifact.source}")
    typer.echo(f"Status: {artifact.status}")
    typer.echo(f"Title: {artifact.title}")
    typer.echo("Body:")
    typer.echo(artifact.body)

    if artifact.reflection_result:
        typer.echo("\nReflection:")
        typer.echo(f"Verdict: {artifact.reflection_result.verdict}")
        if artifact.reflection_result.notes:
            typer.echo("Notes:")
            for note in artifact.reflection_result.notes:
                typer.echo(f"- {note}")

    if artifact.review_result:
        typer.echo("\nReview:")
        typer.echo(f"Category: {artifact.review_result.category}")
        typer.echo(f"Risk: {artifact.review_result.risk}")

        if artifact.review_result.findings:
            typer.echo("Findings:")
            for finding in artifact.review_result.findings:
                typer.echo(f"- {finding}")

        if artifact.review_result.evidence:
            typer.echo("Evidence:")
            for evidence in artifact.review_result.evidence:
                typer.echo(f"- {evidence}")

    if artifact.plan_result:
        typer.echo("\nPlan:")
        typer.echo(f"Decision: {artifact.plan_result.decision}")
        typer.echo(f"Justification: {artifact.plan_result.justification}")

@app.command()
def reviews():
    store = ReviewStore()
    artifacts = store.list_all()

    if not artifacts:
        typer.echo("No reviews found.")
        return

    for artifact in artifacts:
        decision = "N/A"
        if artifact.plan_result:
            decision = artifact.plan_result.decision

        typer.echo(
            f"{artifact.id} | {artifact.category} | {artifact.risk} | "
            f"{decision}"
        )

@app.command()
def show_review(
    review_id: str = typer.Argument(..., help="Review artifact ID"),
):
    store = ReviewStore()

    try:
        artifact = store.get(review_id)
    except FileNotFoundError as e:
        typer.echo(str(e))
        raise typer.Exit(code=1)

    typer.echo(f"ID: {artifact.id}")
    typer.echo(f"Category: {artifact.category}")
    typer.echo(f"Risk: {artifact.risk}")

    if artifact.findings:
        typer.echo("Findings:")
        for finding in artifact.findings:
            typer.echo(f"- {finding}")

    if artifact.evidence:
        typer.echo("Evidence:")
        for evidence in artifact.evidence:
            typer.echo(f"- {evidence}")

    if artifact.plan_result:
        typer.echo("\nPlan:")
        typer.echo(f"Decision: {artifact.plan_result.decision}")
        typer.echo(f"Justification: {artifact.plan_result.justification}")

if __name__ == "__main__":
    app()