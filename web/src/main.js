import "../style.css";
import { loadProfiles, loadProfile } from "./profiles.js";
import { generateFeedback } from "./llm.js";
import { generatePdf } from "./pdf.js";

const STORAGE_KEY_API = "ai-feedback-api-key";
const STORAGE_KEY_BASE = "ai-feedback-api-base";

const $ = (id) => document.getElementById(id);

function show(el, visible) {
  el.classList.toggle("hidden", !visible);
}

function setProgress(text) {
  const el = $("progress");
  el.textContent = text;
  show(el, !!text);
}

async function init() {
  const profileSelect = $("profile-select");
  const profiles = await loadProfiles();
  profileSelect.innerHTML = profiles
    .map((p) => `<option value="${p.id}">${p.name}</option>`)
    .join("");

  const apiKeyInput = $("api-key");
  const apiBaseInput = $("api-base");
  apiKeyInput.value = localStorage.getItem(STORAGE_KEY_API) || "";
  apiBaseInput.value =
    localStorage.getItem(STORAGE_KEY_BASE) || "https://api.openai.com/v1";

  const modeBrowser = $("mode-browser");
  const modeApi = $("mode-api");
  const apiFields = $("api-fields");
  const webllmStatus = $("webllm-status");

  function updateMode() {
    const isApi = modeApi.classList.contains("active");
    show(apiFields, isApi);
    show(webllmStatus, !isApi);
  }

  modeBrowser.addEventListener("click", () => {
    modeBrowser.classList.add("active");
    modeApi.classList.remove("active");
    updateMode();
  });

  modeApi.addEventListener("click", () => {
    modeApi.classList.add("active");
    modeBrowser.classList.remove("active");
    updateMode();
  });

  updateMode();

  const fileInput = $("file-input");
  const notesInput = $("notes");
  $("upload-file").addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    notesInput.value = text;
    fileInput.value = "";
  });

  const generateBtn = $("generate-btn");
  generateBtn.disabled = false;

  generateBtn.addEventListener("click", async () => {
    const candidate = $("candidate").value.trim();
    const notes = notesInput.value.trim();
    const profileId = profileSelect.value;

    if (!candidate) {
      alert("Please enter the candidate name.");
      return;
    }
    if (!notes) {
      alert("Please enter or upload interview notes.");
      return;
    }

    generateBtn.disabled = true;
    setProgress("Loading profile...");

    try {
      const profile = await loadProfile(profileId);
      setProgress("Generating feedback (this may take a minute)...");

      const isApi = modeApi.classList.contains("active");
      const options = {
        mode: isApi ? "api" : "webllm",
        onProgress: (text) => setProgress(text),
      };

      if (isApi) {
        const apiKey = apiKeyInput.value.trim();
        const apiBase = apiBaseInput.value.trim();
        if (!apiKey) {
          alert("Please enter your API key.");
          generateBtn.disabled = false;
          setProgress("");
          return;
        }
        options.apiKey = apiKey;
        options.baseUrl = apiBase || "https://api.openai.com/v1";
        localStorage.setItem(STORAGE_KEY_API, apiKey);
        localStorage.setItem(STORAGE_KEY_BASE, options.baseUrl);
      }

      const report = await generateFeedback(notes, candidate, profile, options);
      setProgress("Generating PDF...");
      generatePdf(report);
      setProgress("Done! PDF downloaded.");
    } catch (err) {
      console.error(err);
      setProgress("");
      alert(`Error: ${err.message}`);
    } finally {
      generateBtn.disabled = false;
    }
  });
}

init();
