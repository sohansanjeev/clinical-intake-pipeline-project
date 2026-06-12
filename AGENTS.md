# AGENTS.md — Clinical Intake Agent

## Build / Test / Lint / Run

```bash
uv sync                                    # Install deps (preferred — faster than pip)
pip install -r requirements.txt            # Alternative install
python -c "from clinical_intake import *"  # Quick import smoke-test
python -m pipeline data/sample.csv data/output.csv  # Run batch extraction
streamlit run app.py                       # Launch Streamlit dashboard
```

No test framework is configured yet. When adding tests, use `pytest` and place
them in `tests/`. No linter or formatter config exists — recommended:
`ruff check . && ruff format .`

## Architecture

**Purpose:** Extract structured intake data (demographics, admission context,
clinical history, triage priority) from raw MIMIC-IV clinical admission notes
using an LLM pipeline. Built for the Vector Institute FastLane MLA scholarship
portfolio.

### Data flow

```
MIMIC-IV CSV          clinical_intake/           Annotated CSV
(text + summary) ──▶  schemas → prompts → chain ──▶  (original +
                       pipeline.py processes       extracted fields)
                       each row via DeepSeek      

                                                        ▶ Streamlit
                                                          dashboard
                                                          (app.py)
```

### Component tree

```
clinical_intake/          Core extraction package
├── __init__.py           Package docstring, no exports yet
├── schemas.py            Pydantic v2 models for structured output
│                          · TriagePriority (enum: low/medium/high)
│                          · PatientDemographics (age, sex)
│                          · AdmissionContext (service, dates)
│                          · ClinicalContext (CC, HPI, PMH, meds, allergies)
│                          · ClinicalIntake (composite wrapper)
├── prompts.py            LLM prompt templates
│                          · SYSTEM_PROMPT (intake clerk role + triage rules)
│                          · HUMAN_PROMPT_TEMPLATE ({note_text} placeholder)
└── chain.py              LangChain LCEL pipeline (stub — build_chain / run_extraction)
pipeline.py               Batch CSV processor (stub — process_csv + CLI entrypoint)
app.py                    Streamlit dashboard (skeleton — triage filter, main area)
dev/sample_data.py        Utility: create N-row sample from mimic_data.csv
data/
├── mimic_data.csv        Full MIMIC-IV notes (361K rows, 2 cols: text, summary)
└── sample.csv            20-row dev subset created via sample_data.py
```

### Important: implementation status

All pipeline functions are **stubs** (`...` bodies). Only schemas, prompts,
and scaffolding are written. The `build_chain()` and `process_csv()` bodies
need to be implemented before anything runs.

## Key Files & Directories

| Path | Role |
|------|------|
| `clinical_intake/` | Deployable package (schemas, prompts, chain) |
| `pipeline.py` | Batch entrypoint for CSV processing |
| `app.py` | Streamlit entrypoint for interactive dashboard |
| `dev/` | Development utilities (not part of deployment) |
| `data/` | Datasets (raw + sample) |
| `.env.example` | LLM API config template (DeepSeek default, OpenAI optional) |
| `crush.json` | CodeWhale LLM provider config (DeepSeek V4 Flash) |
| `requirements.txt` | Pinned Python dependencies |

## Coding Conventions

- **Type hints:** All function signatures annotated (parameters + return).
- **Docstrings:** Module-level docstring + Google-style function docstrings on all public symbols.
- **Optional fields:** Pydantic models use `Optional[T] = None` or
  `Field(default_factory=list)` — never `None` for list fields. LLMs should
  return null rather than hallucinate.
- **Pydantic v2:** `BaseModel` (not `pydantic.BaseSettings`), `Field` for list defaults.
- **Imports:** Standard library → third-party → local. No `*` imports.
- **Path handling:** `pathlib.Path` preferred over `os.path`.
- **String formatting:** f-strings only.
- **Error handling:** Catching should be specific — no bare `except:`. (Not yet enforced in code.)
- **API secrets:** Loaded via `python-dotenv` from `.env` — `DEEPSEEK_API_KEY` env var.

## Git Workflow

- **Branch:** `master` (single-branch workflow, early stage).
- **Commit style:** Lowercase, imperative mood (`created scaffold`,
  `imported mimic dataset, made subset (first 20 rows)`).
- **One author** — solo project, no merge commits yet.

## CI/CD

None configured. LLM API costs make automated CI non-trivial. If adding CI,
recommend running only import-smoke and schema-validation tests, not
full LLM extraction.

## Tips for AI Agents

- **This is a learning project.** The user is using this to learn ML. Always
  explain your reasoning step by step before writing or changing any code.
  Do not implement anything without first discussing the approach and getting
  explicit approval. Treat every change as a teaching opportunity.
- **Ask before changing files.** Never edit, write, or create a file without
  first walking through what you want to do and why, and getting a green light.
- **Pipeline functions are stubs.** Before calling `run_extraction()` or
  `process_csv()`, fill in the `...` bodies in `chain.py` and `pipeline.py`.
- **MIMIC notes span multiple lines.** CSV `text` fields contain embedded
  newlines inside quotes. Use `csv.reader` / `csv.writer` (not pandas' naive
  reader) to avoid row-splitting issues.
- **Sample first.** Always iterate on `data/sample.csv` (20 rows) before
  touching the full 361K-row `data/mimic_data.csv`.
- **DeepSeek is the default LLM.** Configured via `DEEPSEEK_API_KEY` env var.
  The `crush.json` provider config is for CodeWhale's own use, not the
  extraction pipeline.
- **No test infra exists.** If adding tests, they go in `tests/` with
  `pytest`. Mock LLM calls to avoid API costs.
- **Modify schemas with care.** `ClinicalIntake` is the output schema of the
  chain. Adding/removing fields there means updating the prompt +
  `build_chain` parser + `process_csv` output flattening.

<!-- lean-ctx-compression -->
OUTPUT STYLE: dense
- Each statement = one atomic fact line
- Use abbreviations: fn, cfg, impl, deps, req, res, ctx, err, ret
- Diff lines only (+/-/~), never repeat unchanged code
- Symbols: → (causes), + (adds), − (removes), ~ (modifies), ∴ (therefore)
- No narration, no filler, no hedging
- BUDGET: ≤200 tokens per response unless code block required
<!-- /lean-ctx-compression -->
