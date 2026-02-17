# AI Feedback

A CLI tool that generates technical interview feedback reports from free-text notes. Write your interview notes, run the tool, and get a structured PDF report with scores (1-5) and comments for each assessment area.

## Setup

### Download (no install needed)

If you don't want to install Python or run from source:

1. Go to [GitHub Releases](https://github.com/tomasblanarik/ai-feedback/releases) and download the latest release.
2. **Mac:** Download `feedback-macos`. **Windows:** Download `feedback-windows.exe`.
3. Put the file somewhere on your system (e.g. your home folder or a dedicated tools directory).
4. Create a `.env` file in the **same folder** as the executable (or in the directory where you run it). Copy `.env.example` from the repo or create one manually with your API key or LM Studio config (see below).
5. Run from terminal:
   ```bash
   ./feedback-macos generate -i notes.txt -c "John Doe"
   ```
   On Windows: `feedback-windows.exe generate -i notes.txt -c "John Doe"`

### Quick start (from source, macOS/Linux)

```bash
./install.sh
source .venv/bin/activate
# Edit .env with your API key or LM Studio config
```

### Manual setup (from source)

1. Create a virtual environment: `python3 -m venv .venv` then `source .venv/bin/activate`
2. Install: `pip install -e .`
3. Configure: `cp .env.example .env` and edit with your API key or LM Studio URL

### LM Studio (local models)

1. Start LM Studio and load a model (e.g. Llama, Mistral).
2. Click "Start Server" in LM Studio (default: `http://localhost:1234`).
3. In `.env`, set:
   ```
   LLM_BASE_URL=http://localhost:1234/v1
   LLM_MODEL=your-model-name
   OPENAI_API_KEY=lm-studio
   ```
   Use the model name shown in LM Studio (e.g. `meta-llama/Llama-3.2-3B-Instruct`).

**Recommended models (LM Studio):**

- **Qwen 3 8B** or **Ministral 8B** -- best balance of speed and quality (~6GB RAM), reliable at following structured JSON prompts
- **Mistral Small 3.2 (24B)** -- best quality, native JSON output, needs ~14GB RAM
- **Granite 4.0 Tiny (3B)** -- lightest option (~2-3GB RAM), built-in JSON/tool support

Tip: download the GGUF Q4_K_M quantized version for best speed/quality trade-off.

### OpenAI (cloud)

Set `OPENAI_API_KEY` in `.env`. Optionally set `OPENAI_MODEL` to override the default.

**Recommended models (OpenAI):**

- **gpt-4o** (default) -- best quality, supports JSON mode natively
- **gpt-4o-mini** -- cheaper and faster, good enough for this task

## Usage

### Generate a report

```bash
feedback generate --input notes.txt --candidate "John Doe"
```

- `--input` / `-i`: Path to your interview notes file (`.txt` or `.md`)
- `--candidate` / `-c`: Candidate name for the report header
- `--output` / `-o`: Optional output PDF path (default: `feedback-<candidate>-<date>.pdf`)
- `--review` / `-r`: Interactive mode — review and adjust AI-generated scores before PDF generation
- `--config` / `-cfg`: Path to feedback-config.yaml (default: feedback-config.yaml in current directory)

### Review mode

Use `--review` to see the AI-generated scores and optionally adjust them before the PDF is created:

```bash
feedback generate --input notes.txt --candidate "Jane Smith" --review
```

### Show template

View the assessment areas and scoring rubric (from your config or defaults):

```bash
feedback template
```

## Configuration

You can customize the report structure with a `feedback-config.yaml` file. Place it in the directory where you run the tool (or pass `--config /path/to/feedback-config.yaml`).

The config defines:

- **technical** — list of technical assessment areas
- **non_technical** — list of non-technical assessment areas
- **personal_assessment** — list of personal assessment areas (optional)
- **overall_levels** — valid overall levels (e.g. Junior, Medior, Senior, Lead)

Example:

```yaml
technical:
  - "C# Basic"
  - "C# Intermediate"
  - "DBs relational"
  # ... add or remove as needed

non_technical:
  - "Communication"
  - "Self impression"

personal_assessment:
  - "Overall impression"
  - "Cultural fit"
  - "Growth potential"

overall_levels:
  - "Junior"
  - "Medior"
  - "Senior"
  - "Lead"
```

If no config file exists, the tool uses built-in defaults (technical + non-technical only, no personal assessment). Copy `feedback-config.yaml` from the repo as a starting point.

## Assessment Areas (default)

**Technical (12):** C# Basic, C# Intermediate, C# Advanced, DBs relational, DBs no sql, Security, Cloud, Personal projects, Last work project, DevOps, Web development, Web SPA - Angular

**Non-technical (3):** Potential & Motivation (Drive), Communication, Self impression

**Personal Assessment (optional):** Overall impression, Cultural fit, Growth potential — add via config

**Overall:** Level (Junior/Medior/Senior/Lead) + comment

Scoring: 1 = worst, 5 = best. Use N/A when there is not enough data. All areas and levels are configurable via `feedback-config.yaml`.


## Example workflow

1. After an interview, write your notes in `interview-notes.txt`
2. Run: `feedback generate -i interview-notes.txt -c "John Doe" -r`
3. Review the AI-generated scores, adjust if needed
4. PDF is saved as `feedback-John-Doe-20250217-1430.pdf`
5. Share the PDF with HR
