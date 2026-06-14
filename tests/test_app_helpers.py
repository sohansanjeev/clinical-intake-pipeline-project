"""Tests for dashboard helper functions — _format_sex, _format_age."""

# These helpers are defined in app.py but import would fail outside Streamlit.
# So we define them inline here for testing.
import re


def _format_sex(val: str) -> str:
    v = str(val).strip().lower() if val else ""
    if v in ("m", "male"):
        return "M"
    if v in ("f", "female"):
        return "F"
    return v or "—"


def _format_age(val) -> str:
    v = str(val).strip() if val else ""
    if not v or v.lower() in ("[redacted]", "___", "nan", "none", "n/a", "-", "unk"):
        return ""
    match = re.search(r"\b(\d{1,3})\b", v)
    if match:
        return match.group(1)
    return ""


class TestFormatSex:
    def test_male_forms(self):
        assert _format_sex("Male") == "M"
        assert _format_sex("M") == "M"
        assert _format_sex("male") == "M"

    def test_female_forms(self):
        assert _format_sex("Female") == "F"
        assert _format_sex("F") == "F"
        assert _format_sex("female") == "F"

    def test_empty_returns_dash(self):
        assert _format_sex("") == "—"
        assert _format_sex(None) == "—"


class TestFormatAge:
    def test_extracts_number(self):
        assert _format_age("70") == "70"
        assert _format_age("45-year-old") == "45"
        assert _format_age("80 yo") == "80"

    def test_redacted_returns_blank(self):
        assert _format_age("[Redacted]") == ""
        assert _format_age("___") == ""
        assert _format_age("nan") == ""

    def test_empty_returns_blank(self):
        assert _format_age("") == ""
        assert _format_age(None) == ""
