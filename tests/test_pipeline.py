"""Tests for pipeline.py — flattening, serialization, and CSV processing."""

import csv
from pathlib import Path

from clinical_intake.schemas import ClinicalIntake
from pipeline import (
    _serialize,
    _get_flat_columns,
    _flatten_intake,
    _process_one_row,
    process_csv,
)


class TestSerialize:
    def test_none_returns_empty(self):
        assert _serialize(None) == ""

    def test_string_passes_through(self):
        assert _serialize("hello") == "hello"

    def test_int_becomes_string(self):
        assert _serialize(42) == "42"

    def test_enum_becomes_string(self):
        from clinical_intake.schemas import TriagePriority
        assert _serialize(TriagePriority.HIGH) == "high"


class TestGetFlatColumns:
    def test_contains_expected_columns(self):
        cols = _get_flat_columns()
        assert "demographics_age" in cols
        assert "demographics_sex" in cols
        assert "admission_service" in cols
        assert "clinical_context_chief_complaint" in cols
        assert "clinical_context_past_medical_history" in cols
        assert "triage_priority" in cols
        assert "raw_note_snippet" in cols

    def test_total_count(self):
        cols = _get_flat_columns()
        assert len(cols) == 12


class TestFlattenIntake:
    def test_default_instance(self):
        ci = ClinicalIntake()
        flat = _flatten_intake(ci)
        assert flat["demographics_age"] == ""
        assert flat["demographics_sex"] == ""
        assert flat["triage_priority"] == "low"

    def test_populated_instance(self):
        ci = ClinicalIntake(
            demographics={"age": "45", "sex": "Male"},
            triage_priority="high",
            clinical_context={
                "medications": ["aspirin", "metformin"],
                "allergies": [],
            },
        )
        flat = _flatten_intake(ci)
        assert flat["demographics_age"] == "45"
        assert flat["demographics_sex"] == "M"
        assert flat["triage_priority"] == "high"
        assert flat["clinical_context_medications"] == "aspirin; metformin"
        assert flat["clinical_context_allergies"] == ""

    def test_handles_nested_none(self):
        ci = ClinicalIntake(demographics=None)
        flat = _flatten_intake(ci)
        assert flat["demographics_age"] == ""
        assert flat["demographics_sex"] == ""


class TestProcessOneRow:
    def test_returns_flat_dict_and_no_error(self, extraction_chain, sample_csv_rows):
        extracted, error = _process_one_row(extraction_chain, sample_csv_rows[0])
        assert isinstance(extracted, dict)
        assert error == ""
        assert "demographics_age" in extracted

    def test_catches_exception(self, sample_csv_rows):
        from tests.conftest import FakeChatModel
        from clinical_intake.chain import build_chain

        # A fake LLM that returns invalid JSON
        bad_llm = FakeChatModel(response="not valid json")
        bad_chain = build_chain(bad_llm)
        extracted, error = _process_one_row(bad_chain, sample_csv_rows[0])
        assert error != ""


class TestProcessCsv:
    def test_writes_correct_number_of_rows(self, extraction_chain, sample_csv_path, tmp_path, monkeypatch):
        out = tmp_path / "out.csv"
        # Replace build_chain so process_csv uses our mock chain
        import pipeline as ppl
        monkeypatch.setattr(ppl, "build_chain", lambda llm: extraction_chain)
        monkeypatch.setattr(ppl, "ChatOpenAI", lambda *a, **kw: None)

        process_csv(sample_csv_path, str(out), limit=2, concurrent=1)
        with open(out, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2

    def test_output_has_patient_id(self, extraction_chain, sample_csv_path, tmp_path, monkeypatch):
        out = tmp_path / "out.csv"
        import pipeline as ppl
        monkeypatch.setattr(ppl, "build_chain", lambda llm: extraction_chain)
        monkeypatch.setattr(ppl, "ChatOpenAI", lambda *a, **kw: None)

        process_csv(sample_csv_path, str(out), limit=1, concurrent=1)
        with open(out, newline="") as f:
            row = next(csv.DictReader(f))
        assert len(row["patient_id"]) == 6
        assert row["patient_id"].isdigit()

    def test_error_column_present(self, extraction_chain, sample_csv_path, tmp_path, monkeypatch):
        out = tmp_path / "out.csv"
        import pipeline as ppl
        monkeypatch.setattr(ppl, "build_chain", lambda llm: extraction_chain)
        monkeypatch.setattr(ppl, "ChatOpenAI", lambda *a, **kw: None)

        process_csv(sample_csv_path, str(out), limit=1, concurrent=1)
        with open(out, newline="") as f:
            row = next(csv.DictReader(f))
        assert "error" in row
