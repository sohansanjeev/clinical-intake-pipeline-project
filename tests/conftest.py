"""Shared fixtures for clinical intake tests."""
import sys
from pathlib import Path
from typing import Any, Optional

# Add project root to path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

from clinical_intake.chain import build_chain


VALID_LLM_RESPONSE = """{
  "demographics": {"age": "70-year-old", "sex": "Female"},
  "admission": {"service": "Cardiology", "admission_date": null, "discharge_date": null},
  "clinical_context": {
    "chief_complaint": "chest pain",
    "history_of_present_illness": "Patient presents with chest pain",
    "past_medical_history": ["hypertension", "diabetes"],
    "medications": ["aspirin", "metformin"],
    "allergies": []
  },
  "triage_priority": "high",
  "raw_note_snippet": "Chief Complaint: chest pain"
}"""


class FakeChatModel(Runnable):
    """A fake chat model that returns a fixed response string."""

    def __init__(self, response: str = VALID_LLM_RESPONSE):
        self.response = response

    def invoke(self, input: Any, config: Optional[dict] = None, **kwargs: Any) -> AIMessage:
        """Return a fixed AIMessage regardless of input."""
        return AIMessage(content=self.response)


@pytest.fixture
def fake_llm():
    """Return a FakeChatModel that returns a valid ClinicalIntake JSON."""
    return FakeChatModel()


@pytest.fixture
def extraction_chain(fake_llm):
    """Return a built chain using the fake LLM."""
    return build_chain(fake_llm)


@pytest.fixture
def sample_note():
    """Return a dummy clinical note."""
    return "Patient is a 70-year-old female with chest pain."


@pytest.fixture
def sample_csv_path():
    """Path to the 3-row test CSV."""
    return str(PROJECT_ROOT / "tests" / "data" / "test_notes.csv")


@pytest.fixture
def sample_csv_rows():
    """Return a list of dict rows matching test_notes.csv."""
    return [{"text": "dummy note text", "summary": "dummy summary"}] * 3
