# Clinical Intake Agent — Project Plan

## Goal

Build an app that takes raw clinical notes and extracts structured data (demographics, symptoms, triage priority) using an LLM pipeline.

## Architecture

```
Raw text → LangChain pipeline (prompt → LLM → Pydantic parser) → Streamlit dashboard
```

## Components to build

1. **`clinical_intake/schemas.py`** — Pydantic models: `PatientDemographics`, `ClinicalContext`, `ClinicalIntake` with `TriagePriority` enum (Low/Medium/High)

2. **`clinical_intake/prompts.py`** — System prompt instructing LLM to act as a medical intake clerk with triage rules; human prompt takes the raw note

3. **`clinical_intake/chain.py`** — LangChain LCEL pipeline: `prompt | ChatOpenAI(DeepSeek) | PydanticOutputParser`

4. **`app.py`** — Streamlit UI: text area → Process button → structured cards (demographics, clinical context, triage priority badge)

5. **`requirements.txt`** — langchain, langchain-openai, pydantic, streamlit, python-dotenv

## Key learnings

- Structured extraction vs free-form chat
- Pydantic schema design (optional fields, enums, validation)
- Prompt engineering (role setting, output constraints, triage logic)
- LangChain LCEL composability
- Streamlit reactive UI

## Provider

Using DeepSeek (openai-compat) via `DEEPSEEK_API_KEY` env var. Model: `deepseek-chat`.

## Status

Plan finalized. Ready to write code next session.

## Todos

- [ ] **Schemas** — Write `clinical_intake/schemas.py` (PatientDemographics, ClinicalContext, ClinicalIntake, TriagePriority enum)
- [ ] **Prompts** — Write `clinical_intake/prompts.py` (system prompt with triage rules, human prompt template)
- [ ] **Chain** — Write `clinical_intake/chain.py` (LangChain LCEL pipeline: prompt → ChatOpenAI(DeepSeek) → PydanticOutputParser)
- [ ] **App** — Write `app.py` (Streamlit UI: text area, Process button, structured cards)
- [ ] **Deps** — Write `requirements.txt` (langchain, langchain-openai, pydantic, streamlit, python-dotenv)
- [ ] **Install & test** — `pip install -r requirements.txt` and run the app
