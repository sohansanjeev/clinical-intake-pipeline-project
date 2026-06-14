"""Tests for prompts.py — template rendering."""

from clinical_intake.prompts import SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE


class TestSystemPrompt:
    def test_contains_triage_guidelines(self):
        assert "LOW" in SYSTEM_PROMPT
        assert "MEDIUM" in SYSTEM_PROMPT
        assert "HIGH" in SYSTEM_PROMPT

    def test_sets_clerk_role(self):
        assert "intake clerk" in SYSTEM_PROMPT.lower()

    def test_mentions_mimic(self):
        assert "MIMIC" in SYSTEM_PROMPT


class TestHumanPromptTemplate:
    def test_has_note_text_placeholder(self):
        assert "{note_text}" in HUMAN_PROMPT_TEMPLATE

    def test_has_format_instructions_placeholder(self):
        assert "{format_instructions}" in HUMAN_PROMPT_TEMPLATE

    def test_renders_with_variables(self):
        rendered = HUMAN_PROMPT_TEMPLATE.format(
            note_text="test note",
            format_instructions="return JSON",
        )
        assert "test note" in rendered
        assert "return JSON" in rendered
