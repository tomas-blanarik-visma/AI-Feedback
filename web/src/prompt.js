/**
 * Build system and user prompts for the LLM.
 * Ported from src/ai_feedback/llm.py
 */

/**
 * @param {Object} profile - { technical, non_technical, personal_assessment, overall_levels }
 * @returns {string}
 */
export function buildSystemPrompt(profile) {
  const lines = [
    "You are an expert technical interviewer evaluating candidates. Your task is to analyze interview notes and produce structured feedback scores.",
    "",
    "Scoring rubric (1 = worst, 5 = best):",
    "- 1: No knowledge/demonstrated ability, major red flags",
    "- 2: Limited knowledge, significant gaps, below expectations",
    "- 3: Adequate knowledge, meets basic expectations, some gaps",
    "- 4: Good knowledge, above average, minor gaps",
    "- 5: Strong/excellent knowledge, exceeds expectations, no significant gaps",
    "",
    "For each assessment area, provide a score (1-5) and a brief comment (1-2 sentences) explaining why you gave that score based on the interview notes. Be objective and cite specific evidence from the notes when possible.",
    "",
    "For non-technical and personal assessment areas, infer scores from behavioral cues and personality observations in the notes. Only use null when there is absolutely no information to infer a score. Behavioral observations and personality descriptions count as evidence.",
    "",
    "You MUST return scores for ALL of these areas exactly as named:",
    "",
    "Technical areas:",
    ...profile.technical.map((a) => `- ${a}`),
    "",
    "Non-technical areas:",
    ...profile.non_technical.map((a) => `- ${a}`),
  ];

  if (profile.personal_assessment?.length) {
    lines.push("", "Personal assessment areas:");
    profile.personal_assessment.forEach((a) => lines.push(`- ${a}`));
  }

  const levelsStr = profile.overall_levels.join(", ");
  lines.push(
    "",
    `Also provide an overall_level (one of: ${levelsStr}) and an overall_comment (2-4 sentences) summarizing the candidate's strengths, weaknesses, and hiring recommendation.`
  );

  return lines.join("\n");
}

/**
 * @param {string} notes
 * @param {string} candidateName
 * @param {Object} profile
 * @returns {string}
 */
export function buildUserPrompt(notes, candidateName, profile) {
  const jsonParts = [
    `  "candidate_name": "${candidateName}",`,
    '  "technical_scores": [{"name": "<area>", "score": <1-5 or null>, "comment": "<explanation>"}],',
    '  "non_technical_scores": [{"name": "<area>", "score": <1-5 or null>, "comment": "<explanation>"}],',
  ];

  if (profile.personal_assessment?.length) {
    jsonParts.push(
      '  "personal_assessment_scores": [{"name": "<area>", "score": <1-5 or null>, "comment": "<explanation>"}],'
    );
  }

  const levelsStr = profile.overall_levels.join("|");
  jsonParts.push(
    `  "overall_level": "<${levelsStr}>",`,
    '  "overall_comment": "<2-4 sentence overall assessment>"'
  );

  const jsonStruct = "{\n" + jsonParts.join("\n") + "\n}";

  let areaCounts = `${profile.technical.length} technical, ${profile.non_technical.length} non-technical`;
  if (profile.personal_assessment?.length) {
    areaCounts += `, ${profile.personal_assessment.length} personal assessment`;
  }

  return `Candidate: ${candidateName}

Interview notes:
---
${notes}
---

Analyze these notes and return a JSON object with this exact structure:
${jsonStruct}

Use score: null and comment: "Not evaluated/not enough data" when there is insufficient evidence. Include all ${areaCounts} areas in the exact order listed in the system prompt.`;
}
