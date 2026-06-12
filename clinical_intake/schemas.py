"""
Pydantic v2 models for clinical intake extraction.

Schemas define the structured output the LLM extracts from raw MIMIC-IV
admission notes. Fields are intentionally permissive (most are Optional)
because clinical notes are inconsistent — the LLM should return None rather
than hallucinate missing data.

Classes:
    TriagePriority: Low / Medium / High severity enum (LLM-inferred).
    PatientDemographics: Extracted patient attributes (age, sex).
    AdmissionContext: Service, admission/discharge dates.
    ClinicalContext: Chief complaint, HPI, PMH, medications, allergies.
    ClinicalIntake: Composite output wrapping all of the above.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class TriagePriority(str, Enum):
    """Clinical urgency inferred from the note's symptom language and context."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PatientDemographics(BaseModel):
    """Patient-level attributes extractable from an admission note.

    MIMIC-IV notes have personally-identifying fields redacted (name,
    DOB), but sex and approximate age (e.g. "70-year-old") are present.
    """
    age: Optional[str] = None
    sex: Optional[str] = None


class AdmissionContext(BaseModel):
    """Admission-level metadata: service type and dates."""
    service: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None


class ClinicalContext(BaseModel):
    """Core clinical content extracted from the note body."""
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    past_medical_history: Optional[list[str]] = Field(default_factory=list)
    medications: Optional[list[str]] = Field(default_factory=list)
    allergies: Optional[list[str]] = Field(default_factory=list)


class ClinicalIntake(BaseModel):
    """Complete structured output from the extraction pipeline."""
    demographics: Optional[PatientDemographics] = None
    admission: Optional[AdmissionContext] = None
    clinical_context: Optional[ClinicalContext] = None
    triage_priority: TriagePriority = TriagePriority.LOW
    raw_note_snippet: str = ""
