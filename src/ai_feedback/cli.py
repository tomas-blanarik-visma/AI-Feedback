"""CLI entry point for the AI feedback tool."""

import logging
from datetime import datetime
from pathlib import Path

import typer

from .llm import analyze_interview_notes
from .models import AreaScore, FeedbackReport
from .pdf_generator import generate_pdf
from .profile import FeedbackProfile, load_profile

app = typer.Typer(help="Generate interview feedback reports from notes using AI.")


def _format_report_for_display(report: FeedbackReport) -> str:
    """Format a report for display in the terminal."""
    lines = [f"\n=== Feedback for {report.candidate_name} ===\n"]
    lines.append("Technical:")
    for s in report.technical_scores:
        lines.append(f"  {s.name}: {s.display_score} - {s.comment}")
    lines.append("\nNon-technical:")
    for s in report.non_technical_scores:
        lines.append(f"  {s.name}: {s.display_score} - {s.comment}")
    if report.personal_assessment_scores:
        lines.append("\nPersonal Assessment:")
        for s in report.personal_assessment_scores:
            lines.append(f"  {s.name}: {s.display_score} - {s.comment}")
    lines.append("\nOverall:")
    lines.append(f"  Level: {report.overall_level}")
    lines.append(f"  Comment: {report.overall_comment}")
    if report.ai_evaluation:
        lines.append("\nAI Evaluation:")
        for line in report.ai_evaluation.splitlines():
            lines.append(f"  {line}")
        lines.append("")
    else:
        lines.append("")
    return "\n".join(lines)


def _interactive_review(
    report: FeedbackReport, profile: FeedbackProfile
) -> FeedbackReport:
    """Allow user to interactively adjust scores before generating PDF."""
    typer.echo(_format_report_for_display(report))
    typer.echo(
        "Review the scores above. For each area, enter a new score (1-5), 'n' for N/A, or 'Enter' to keep. "
        "Type 'q' to skip remaining and generate PDF.\n"
    )

    updated_technical: list[AreaScore] = []
    updated_non_technical: list[AreaScore] = []
    updated_personal: list[AreaScore] = []

    def process_scores(scores: list[AreaScore], updated: list[AreaScore]) -> bool:
        """Process scores, return False if user typed 'q'."""
        for idx, score in enumerate(scores):
            while True:
                user_input = typer.prompt(
                    f"{score.name} [{score.display_score}]: ",
                    default="",
                    show_default=False,
                )
                if user_input.lower() == "q":
                    updated.extend(
                        AreaScore(name=s.name, score=s.score, comment=s.comment)
                        for s in scores[idx:]
                    )
                    return False
                if user_input.strip() == "":
                    updated.append(score)
                    break
                if user_input.lower() == "n":
                    updated.append(
                        AreaScore(
                            name=score.name,
                            score=None,
                            comment="Not evaluated/not enough data",
                        )
                    )
                    break
                try:
                    new_score = int(user_input.strip())
                    if 1 <= new_score <= 5:
                        new_comment = typer.prompt(
                            f"  Comment: ",
                            default=score.comment,
                            show_default=False,
                        )
                        updated.append(
                            AreaScore(
                                name=score.name,
                                score=new_score,
                                comment=new_comment or score.comment,
                            )
                        )
                        break
                    else:
                        typer.echo("Score must be between 1 and 5.")
                except ValueError:
                    typer.echo(
                        "Enter 1-5, 'n' for N/A, Enter to keep, or 'q' to finish."
                    )
        return True

    if process_scores(report.technical_scores, updated_technical):
        if process_scores(report.non_technical_scores, updated_non_technical):
            process_scores(report.personal_assessment_scores, updated_personal)
        else:
            updated_non_technical.extend(report.non_technical_scores)
            updated_personal.extend(report.personal_assessment_scores)
    else:
        updated_non_technical.extend(report.non_technical_scores)
        updated_personal.extend(report.personal_assessment_scores)

    # Overall level and comment
    level_input = typer.prompt(
        f"\nOverall level [{report.overall_level}]",
        default=report.overall_level,
        show_default=True,
    )
    level = level_input.strip() if level_input else report.overall_level
    if level not in profile.overall_levels:
        level = report.overall_level

    comment_input = typer.prompt(
        "Overall comment",
        default=report.overall_comment,
        show_default=False,
    )
    overall_comment = comment_input or report.overall_comment

    return FeedbackReport(
        candidate_name=report.candidate_name,
        technical_scores=updated_technical,
        non_technical_scores=updated_non_technical,
        personal_assessment_scores=updated_personal,
        overall_level=level,
        overall_comment=overall_comment,
        ai_evaluation=report.ai_evaluation,
    )


@app.command()
def generate(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        path_type=Path,
        exists=True,
        help="Path to interview notes file (txt or md)",
    ),
    candidate: str = typer.Option(
        ...,
        "--candidate",
        "-c",
        help="Name of the candidate",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        path_type=Path,
        help="Output PDF path (overrides --output-folder when set)",
    ),
    output_folder: Path = typer.Option(
        Path("output"),
        "--output-folder",
        "-d",
        path_type=Path,
        help="Folder for generated PDFs when --output is not set (default: output)",
    ),
    review: bool = typer.Option(
        False,
        "--review",
        "-r",
        help="Interactive mode: review and adjust scores before generating PDF",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-cfg",
        path_type=Path,
        exists=True,
        help="Path to feedback-config.yaml (default: feedback-config.yaml in cwd)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable debug logging",
    ),
) -> None:
    """Generate a feedback report from interview notes."""
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(name)s | %(levelname)s | %(message)s",
        )
        logging.getLogger("ai_feedback").setLevel(logging.DEBUG)
        # Reduce noise from third-party libraries
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

    notes_text = input.read_text(encoding="utf-8")
    profile = load_profile(config)

    with typer.progressbar(
        length=1,
        label="Analyzing interview notes",
        show_eta=False,
    ) as progress:
        report = analyze_interview_notes(notes_text, candidate, profile)
        progress.update(1)

    if review:
        report = _interactive_review(report, profile)

    if output is not None:
        out_path = output
    else:
        output_folder.mkdir(parents=True, exist_ok=True)
        out_path = output_folder / (
            f"feedback-{candidate.replace(' ', '-')}-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf"
        )
    generate_pdf(report, out_path)
    typer.echo(f"Report saved to {out_path}")


@app.command()
def template(
    config: Path | None = typer.Option(
        None,
        "--config",
        "-cfg",
        path_type=Path,
        exists=True,
        help="Path to feedback-config.yaml (default: feedback-config.yaml in cwd)",
    ),
) -> None:
    """Show the assessment areas and scoring rubric."""
    profile = load_profile(config)
    typer.echo("Interview Feedback Template - Assessment Areas\n")
    typer.echo("Scoring: 1 = worst, 5 = best\n")
    typer.echo("Technical:")
    for area in profile.technical:
        typer.echo(f"  - {area}")
    typer.echo("\nNon-technical:")
    for area in profile.non_technical:
        typer.echo(f"  - {area}")
    if profile.personal_assessment:
        typer.echo("\nPersonal Assessment:")
        for area in profile.personal_assessment:
            typer.echo(f"  - {area}")
    levels_str = "/".join(profile.overall_levels)
    typer.echo(f"\nOverall: Level ({levels_str}) + comment")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
