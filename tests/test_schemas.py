"""Tests for schemas.py — Pydantic models and TriagePriority enum."""

from clinical_intake.schemas import (
    TriagePriority,
    PatientDemographics,
    AdmissionContext,
    ClinicalContext,
    ClinicalIntake,
)


class TestTriagePriority:
    def test_values(self):
        assert TriagePriority.LOW.value == "low"
        assert TriagePriority.MEDIUM.value == "medium"
        assert TriagePriority.HIGH.value == "high"

    def test_severity_score(self):
        assert TriagePriority.LOW.severity_score == 1
        assert TriagePriority.MEDIUM.severity_score == 2
        assert TriagePriority.HIGH.severity_score == 3

    def test_str_enum_coercion(self):
        # str enum allows direct string comparison
        assert TriagePriority.LOW == "low"
        assert TriagePriority("high") == TriagePriority.HIGH


class TestPatientDemographics:
    def test_defaults(self):
        d = PatientDemographics()
        assert d.age is None
        assert d.sex is None

    def test_populated(self):
        d = PatientDemographics(age="45", sex="Male")
        assert d.age == "45"
        assert d.sex == "Male"


class TestAdmissionContext:
    def test_defaults(self):
        a = AdmissionContext()
        assert a.service is None
        assert a.admission_date is None
        assert a.discharge_date is None


class TestClinicalContext:
    def test_list_defaults_are_empty_lists_not_none(self):
        c = ClinicalContext()
        assert c.past_medical_history == []
        assert c.medications == []
        assert c.allergies == []

    def test_single_fields_default_to_none(self):
        c = ClinicalContext()
        assert c.chief_complaint is None
        assert c.history_of_present_illness is None


class TestClinicalIntake:
    def test_default_triage(self):
        ci = ClinicalIntake()
        assert ci.triage_priority == TriagePriority.LOW

    def test_default_snippet(self):
        ci = ClinicalIntake()
        assert ci.raw_note_snippet == ""

    def test_accepts_nested_dicts(self):
        ci = ClinicalIntake(
            demographics={"age": "30", "sex": "F"},
            admission={"service": "UROLOGY"},
            clinical_context={"chief_complaint": "renal mass"},
            triage_priority="low",
        )
        assert ci.demographics.age == "30"
        assert ci.demographics.sex == "F"
        assert ci.admission.service == "UROLOGY"
        assert ci.clinical_context.chief_complaint == "renal mass"
        assert ci.triage_priority == TriagePriority.LOW

    def test_model_dump_json_mode(self):
        ci = ClinicalIntake(triage_priority="high")
        data = ci.model_dump(mode="json")
        assert data["triage_priority"] == "high"
        assert data["demographics"] is None
