/**
 * PDF generation using jsPDF + AutoTable.
 * Replicates layout from src/ai_feedback/pdf_generator.py
 */

import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";

function displayScore(score) {
  return score == null ? "N/A" : String(score);
}

function createScoreTable(doc, scores, colWidths, startY) {
  const [nameW, evalW, commentW] = colWidths;
  const head = [["Name", "Evaluation", "Comment"]];
  const body = scores.map((s) => [s.name, displayScore(s.score), s.comment]);

  autoTable(doc, {
    head,
    body,
    startY: startY ?? (doc.lastAutoTable ? doc.lastAutoTable.finalY + 8 : undefined),
    theme: "grid",
    headStyles: {
      fillColor: [68, 114, 196],
      textColor: 255,
      fontStyle: "bold",
      fontSize: 10,
    },
    bodyStyles: {
      fontSize: 9,
    },
    columnStyles: {
      0: { cellWidth: nameW },
      1: { cellWidth: evalW, halign: "center" },
      2: { cellWidth: commentW },
    },
    alternateRowStyles: {
      fillColor: [242, 242, 242],
    },
    margin: { left: 15, right: 15 },
  });
}

/**
 * Generate PDF from feedback report and trigger download.
 * @param {Object} report - { candidate_name, technical_scores, non_technical_scores, personal_assessment_scores, overall_level, overall_comment, ai_evaluation }
 */
export function generatePdf(report) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const margin = 15;
  const pageWidth = doc.internal.pageSize.getWidth();
  const colWidths = [40, 20, 100];

  let y = margin;

  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.text(`Interview Feedback: ${report.candidate_name}`, margin, y);
  y += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text("1 - worst, 5 - best", margin, y);
  y += 10;

  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Technical:", margin, y);
  y += 6;

  createScoreTable(doc, report.technical_scores, colWidths, y);
  y = doc.lastAutoTable.finalY + 10;

  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Non-technical:", margin, y);
  y += 6;

  createScoreTable(doc, report.non_technical_scores, colWidths, y);
  y = doc.lastAutoTable.finalY + 10;

  if (report.personal_assessment_scores?.length) {
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.text("Personal Assessment:", margin, y);
    y += 6;

    createScoreTable(doc, report.personal_assessment_scores, colWidths, y);
    y = doc.lastAutoTable.finalY + 10;
  }

  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text(`Overall assessment: ${report.overall_level}`, margin, y);
  y += 6;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  const overallLines = doc.splitTextToSize(
    report.overall_comment,
    pageWidth - 2 * margin
  );
  doc.text(overallLines, margin, y);
  y += overallLines.length * 5 + 10;

  if (report.ai_evaluation) {
    doc.setFontSize(11);
    doc.setFont("helvetica", "italic");
    doc.setTextColor(85, 85, 85);
    doc.text("AI Evaluation", margin, y);
    y += 6;

    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    const aiLines = doc.splitTextToSize(
      report.ai_evaluation,
      pageWidth - 2 * margin
    );
    doc.text(aiLines, margin, y);
    doc.setTextColor(0, 0, 0);
  }

  const filename = `feedback-${report.candidate_name.replace(/\s+/g, "-")}-${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(filename);
}
