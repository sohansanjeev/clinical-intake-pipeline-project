# Clinical Intake Extraction Pipeline

LLM-powered structured data extraction from MIMIC-IV clinical admission notes.

## Pipeline Overview

```
MIMIC-IV CSV          clinical_intake/               Annotated CSV
(text + summary) ──▶  schemas → prompts → chain ──▶  (original +
                       pipeline.py processes       extracted fields)
                       each row via DeepSeek v4        │
                       Flash (5 concurrent              ▶ Streamlit
                       workers)                        dashboard
```

The pipeline takes raw MIMIC-IV admission notes, sends each through a
LangChain LCEL chain (prompt template → ChatOpenAI → PydanticOutputParser),
and writes the structured output back to a CSV alongside the original data.
A Streamlit dashboard provides interactive browsing with pagination,
triage filtering, and patient detail cards.

## Architecture & Design Decisions

### `csv.reader` over pandas

MIMIC notes contain embedded newlines inside quoted CSV fields. A naive
`pd.read_csv()` splits on those newlines and corrupts rows. Python's
`csv.DictReader` handles quoted fields correctly.

### `summary` column as LLM input

Each note has a `text` (full note) and a `summary` (LLM-generated summary)
column. Feeding the summary instead of the full text is ~2× faster and
produces equivalent extraction quality. Both columns are preserved in the
output for reference.

### Parallel processing

Processing 100 rows sequentially takes ~70s. With `ThreadPoolExecutor(5)`
the same work completes in ~20s — a 3.5× speedup with no accuracy loss.

### Sex and age normalization

Converting Male/Female → M/F and extracting age numbers (45-year-old → 45)
happens at the pipeline level in shared utility functions. The dashboard
imports the same functions rather than duplicating the logic.

### Single-file Streamlit dashboard

Streamlit's multi-page mode generates an automatic sidebar navigation menu.
Using conditional rendering in a single file (`app.py`) gives full control
over the layout — a clean landing page with no sidebar, then a sidebar-only
dashboard view after upload.

### Random patient IDs

IDs are random 6-digit zero-padded numbers (`random.randint(1, 999999)`)
rather than sequential. This avoids implying that row order reflects
admission order or severity.

### Custom `FakeChatModel` for tests

LangChain 1.2.7 (the version resolved by the project dependencies) doesn't
export `FakeMessagesListLLM`. Tests use a custom `FakeChatModel(Runnable)`
that returns a fixed JSON response. This keeps all 42 tests free and
zero-cost.

### Prompt engineering

- System prompt instructs `null` for missing data to prevent hallucination
- Triage rubric uses symptom language: active chest pain / suicidal ideation
  → HIGH, vague complaints → LOW
- Uses `with_structured_output(method="json_schema")` to enforce the output
  schema at the API level rather than parsing free-text JSON

## Known Limitations

- **Memory**: `csv.DictReader` reads all rows into memory via `list()`. For
  the full 361K-row dataset this is ~3-4 GB. A streaming approach would be
  needed for production.
- **No CI/CD**: API costs make automated LLM testing non-trivial.
  Import-smoke and schema-validation tests could run in CI, but full
  extraction tests require a real API key.
- **Allergies**: 1 miss in 10-row evaluation (omeprazole). Prompt tuning
  could improve recall.
- **Age demo uses synthetic data**: MIMIC-IV redacts ages, so proof of
  age extraction required creating artificial notes with explicit ages.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # add your DEEPSEEK_API_KEY
python -m pipeline data/sample.csv data/output.csv --limit 5 --concurrent 1
streamlit run app.py
```

## Tests

```bash
python -m pytest tests/ -v
```

42 tests, zero API calls (LLM is mocked).

## Age Extraction

MIMIC-IV redacts all patient ages (`___` / `[Redacted]`). The LLM correctly
leaves the age field empty when no age is present in the note.

To verify the LLM **can** extract age when it is present:

```bash
python -m pipeline data/age_demo.csv data/age_demo_output.csv --concurrent 1
```

This runs 3 synthetic notes against the real LLM (`data/age_demo_output.csv`)
and confirms age is captured. The pipeline normalizes age to a number-only
string via `normalize_age()` (regex extracts the first 1-3 digit sequence):

| Input text                         | Raw LLM output | Stored as |
|------------------------------------|----------------|-----------|
| `45-year-old female with headache` | `45-year-old`  | `45` ✅   |
| `30 yo male with ACL tear`         | `30`           | `30` ✅   |
| `80-year-old woman with syncope`   | `80`           | `80` ✅   |

Post-processing normalizes all age formats at the pipeline level before
writing to CSV. No cleaning needed in downstream consumers.

## Evaluation

Extraction quality was spot-checked on 10 rows from `data/sample.csv`
(`data/sample_evaluate_output.csv`). Results are indicative, not
statistically significant — 10 rows is too small for formal accuracy claims.

| Field        | Correct | Notes                                |
|--------------|---------|--------------------------------------|
| Sex          | 10/10   | Normalized to M/F at pipeline level  |
| Service      | 10/10   |                                      |
| Chief Compl. | 10/10   |                                      |
| Triage       | 8-9/10  | All clinically reasonable            |
| Age          | 10/10   | Correctly empty — redacted in source |
| PMH / Meds   | 10/10   | Well extracted                       |
| Allergies    | 9/10    | 1 miss (omeprazole)                  |

Exploratory analysis plots generated from the 100-row output are available in
[`plots/`](plots/?v=2). These include triage distribution, triage by service,
sex distribution, top complaints, top medications, top conditions, triage by
sex, and service volume.
