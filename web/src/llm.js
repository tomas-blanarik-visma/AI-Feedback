/**
 * LLM abstraction - WebLLM (in-browser) and BYOK (API key) modes.
 */

import { CreateMLCEngine } from "@mlc-ai/web-llm";
import { buildSystemPrompt, buildUserPrompt } from "./prompt.js";

const WEBLLM_MODEL = "Llama-3.2-3B-Instruct-q4f16_1-MLC";

let webllmEngine = null;

function extractJson(text) {
  const trimmed = text.trim();
  const codeBlockMatch = trimmed.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
  if (codeBlockMatch) return codeBlockMatch[1];
  const objectMatch = trimmed.match(/(\{[\s\S]*\})/);
  if (objectMatch) return objectMatch[1];
  return trimmed;
}

function matches(respName, canonical) {
  const norm = (s) =>
    s
      .toLowerCase()
      .trim()
      .replace(/a\.k\.a\./g, "aka")
      .replace(/a\.k\.a/g, "aka");
  return norm(respName) === norm(canonical);
}

function parseScore(val) {
  if (val == null) return null;
  if (typeof val === "number" && val >= 1 && val <= 5) return val;
  return null;
}

function parseComment(val) {
  return typeof val === "string" ? val : "Not evaluated/not enough data";
}

function parseScores(dataKey, areas, data) {
  const raw = data[dataKey] || [];
  return areas.map((area) => {
    const found = raw.find((s) => matches(s.name || "", area));
    if (found) {
      return {
        name: area,
        score: parseScore(found.score),
        comment: parseComment(found.comment),
      };
    }
    return {
      name: area,
      score: null,
      comment: "Not evaluated/not enough data",
    };
  });
}

function parseResponse(content, profile, candidateName) {
  const jsonStr = extractJson(content);
  let data = {};
  try {
    data = JSON.parse(jsonStr || "{}");
  } catch {
    throw new Error("Failed to parse LLM response as JSON");
  }

  const technicalScores = parseScores("technical_scores", profile.technical, data);
  const nonTechnicalScores = parseScores(
    "non_technical_scores",
    profile.non_technical,
    data
  );
  let personalAssessmentScores = [];
  if (profile.personal_assessment?.length) {
    personalAssessmentScores = parseScores(
      "personal_assessment_scores",
      profile.personal_assessment,
      data
    );
  }

  const defaultLevel = profile.overall_levels[0] || "Medior";
  let overallLevel = data.overall_level || defaultLevel;
  if (!profile.overall_levels.includes(overallLevel)) {
    overallLevel = defaultLevel;
  }

  return {
    candidate_name: data.candidate_name || candidateName,
    technical_scores: technicalScores,
    non_technical_scores: nonTechnicalScores,
    personal_assessment_scores: personalAssessmentScores,
    overall_level: overallLevel,
    overall_comment: data.overall_comment || "See interview notes for details.",
    ai_evaluation: "",
  };
}

/**
 * Generate feedback using WebLLM (in-browser model).
 */
async function generateWithWebLLM(notes, candidateName, profile, options = {}) {
  const { onProgress } = options;

  if (!webllmEngine) {
    const initProgressCallback = (report) => {
      if (onProgress) onProgress(report.text || JSON.stringify(report));
    };
    webllmEngine = await CreateMLCEngine(WEBLLM_MODEL, {
      initProgressCallback,
    });
  }

  const systemPrompt = buildSystemPrompt(profile);
  const userPrompt = buildUserPrompt(notes, candidateName, profile);

  const reply = await webllmEngine.chat.completions.create({
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ],
    temperature: 0.3,
    max_tokens: 4096,
    response_format: { type: "json_object" },
  });

  const content = reply.choices?.[0]?.message?.content || "";
  return parseResponse(content, profile, candidateName);
}

/**
 * Generate feedback using API (BYOK).
 */
async function generateWithAPI(notes, candidateName, profile, options = {}) {
  const { apiKey, baseUrl = "https://api.openai.com/v1", model = "gpt-4o" } =
    options;

  if (!apiKey) {
    throw new Error("API key is required");
  }

  const systemPrompt = buildSystemPrompt(profile);
  const userPrompt = buildUserPrompt(notes, candidateName, profile);

  const url = baseUrl.replace(/\/$/, "") + "/chat/completions";
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      temperature: 0.3,
      max_tokens: 4096,
      response_format: { type: "json_object" },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`API error ${response.status}: ${err}`);
  }

  const data = await response.json();
  const content = data.choices?.[0]?.message?.content || "";
  return parseResponse(content, profile, candidateName);
}

/**
 * Generate feedback report.
 * @param {string} notes - Interview notes
 * @param {string} candidateName - Candidate name
 * @param {Object} profile - Assessment profile
 * @param {Object} options - { mode: 'webllm'|'api', apiKey?, baseUrl?, model?, onProgress? }
 */
export async function generateFeedback(
  notes,
  candidateName,
  profile,
  options = {}
) {
  const { mode = "webllm" } = options;

  if (mode === "api") {
    return generateWithAPI(notes, candidateName, profile, options);
  }
  return generateWithWebLLM(notes, candidateName, profile, options);
}

export { WEBLLM_MODEL };
