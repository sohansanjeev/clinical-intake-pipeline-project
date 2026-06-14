"""Tests for chain.py — build_chain and run_extraction."""

import os

import pytest
from langchain_core.runnables import Runnable

from clinical_intake.chain import build_chain, run_extraction
from clinical_intake.schemas import ClinicalIntake


class TestBuildChain:
    def test_returns_runnable(self, fake_llm):
        chain = build_chain(fake_llm)
        assert isinstance(chain, Runnable)

    def test_invoke_returns_clinical_intake(self, extraction_chain, sample_note):
        result = extraction_chain.invoke({"note_text": sample_note})
        assert isinstance(result, ClinicalIntake)

    def test_invoke_populates_fields(self, extraction_chain, sample_note):
        result = extraction_chain.invoke({"note_text": sample_note})
        assert result.demographics.age == "70-year-old"
        assert result.demographics.sex == "Female"
        assert result.triage_priority == "high"


class TestRunExtraction:
    def test_raises_without_api_key(self):
        # Ensure no env var is set during this test
        original = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            with pytest.raises(ValueError, match="DEEPSEEK_API_KEY not set"):
                run_extraction("test note")
        finally:
            if original:
                os.environ["DEEPSEEK_API_KEY"] = original
