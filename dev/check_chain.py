"""Smoke test: verify chain.py and prompts.py import correctly."""
from clinical_intake.schemas import ClinicalIntake
from clinical_intake.prompts import SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE
from clinical_intake.chain import build_chain

# Check prompt has the format_instructions placeholder
assert "{format_instructions}" in HUMAN_PROMPT_TEMPLATE, \
    "Missing format_instructions placeholder in human prompt"
print("✅ HUMAN_PROMPT_TEMPLATE has format_instructions placeholder")

# Check we can construct schema
schema = ClinicalIntake(
    triage_priority="low",
    raw_note_snippet="test"
)
assert schema.triage_priority.value == "low"
print(f"✅ ClinicalIntake schema works: triage={schema.triage_priority.value}, severity={schema.triage_priority.severity_score}")

# Check build_chain arguments
import inspect
sig = inspect.signature(build_chain)
params = list(sig.parameters.keys())
assert "llm" in params
print(f"✅ build_chain() accepts: {params}")

print("\nAll checks passed!")
