"""PDF report generation using ReportLab."""

import logging
from pathlib import Path

from reportlab.lib import colors

logger = logging.getLogger("ai_feedback.pdf_generator")
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AreaScore, FeedbackReport


def _create_score_table(
    areas: list[AreaScore], col_widths: list[float], cell_style: ParagraphStyle
) -> Table:
    """Create a table for a set of assessment areas."""
    data = [["Name", "Evaluation", "Comment"]]
    for area in areas:
        data.append(
            [
                Paragraph(area.name, cell_style),
                area.display_score,
                Paragraph(area.comment, cell_style),
            ]
        )

    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def generate_pdf(report: FeedbackReport, output_path: Path) -> None:
    """
    Generate a PDF report from a FeedbackReport.

    Args:
        report: The feedback report with scores and comments
        output_path: Path where the PDF will be saved
    """
    logger.debug(
        "Generating PDF: %s (technical=%d non_technical=%d)",
        output_path,
        len(report.technical_scores),
        len(report.non_technical_scores),
    )
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
    )

    # Title with candidate name
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
    )
    elements.append(Paragraph(f"Interview Feedback: {report.candidate_name}", title_style))
    elements.append(Paragraph("1 - worst, 5 - best", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Technical section
    tech_header = ParagraphStyle(
        "TechHeader",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=6,
    )
    elements.append(Paragraph("Technical:", tech_header))

    col_widths = [4 * cm, 2 * cm, 10 * cm]
    elements.append(
        _create_score_table(report.technical_scores, col_widths, cell_style)
    )
    elements.append(Spacer(1, 0.5 * cm))

    # Non-technical section
    elements.append(Paragraph("Non-technical:", tech_header))
    elements.append(
        _create_score_table(report.non_technical_scores, col_widths, cell_style)
    )
    elements.append(Spacer(1, 0.5 * cm))

    # Personal assessment section (conditional)
    if report.personal_assessment_scores:
        elements.append(Paragraph("Personal Assessment:", tech_header))
        elements.append(
            _create_score_table(
                report.personal_assessment_scores, col_widths, cell_style
            )
        )
        elements.append(Spacer(1, 0.5 * cm))

    # Overall assessment
    overall_header_style = ParagraphStyle(
        "OverallHeader",
        parent=tech_header,
        fontSize=12,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    elements.append(
        Paragraph(
            f"Overall assessment: {report.overall_level}",
            overall_header_style,
        )
    )
    overall_style = ParagraphStyle(
        "Overall",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=12,
    )
    elements.append(Paragraph(report.overall_comment, overall_style))

    # AI Evaluation section
    if report.ai_evaluation:
        elements.append(Spacer(1, 0.5 * cm))
        ai_header_style = ParagraphStyle(
            "AIEvalHeader",
            parent=tech_header,
            fontSize=11,
            fontName="Helvetica-Oblique",
            textColor=colors.HexColor("#555555"),
            spaceAfter=4,
        )
        elements.append(Paragraph("AI Evaluation", ai_header_style))
        ai_eval_style = ParagraphStyle(
            "AIEval",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            spaceAfter=12,
        )
        elements.append(Paragraph(report.ai_evaluation, ai_eval_style))

    doc.build(elements)
    logger.debug("PDF saved to %s", output_path)
