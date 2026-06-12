"""
LangChain extraction pipeline — prompt → LLM → Pydantic parser.

Builds an LCEL chain that takes a raw note text, sends it through the
prompt template to DeepSeek (openai-compatible API), and parses the
output into a ClinicalIntake Pydantic model.

Exports:
    build_chain: Factory that constructs the pipeline given an LLM instance.
    run_extraction: Convenience function: LLM setup → chain → result.
"""

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from clinical_intake.schemas import ClinicalIntake
from clinical_intake.prompts import SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE


def build_chain(llm: ChatOpenAI) -> Runnable:
    """Construct the extraction chain: prompt template → LLM → parser.

    Args:
        llm: A configured ChatOpenAI instance (pointed at DeepSeek).

    Returns:
        An LCEL Runnable that accepts a dict with a "note_text" key
        and returns a ClinicalIntake instance.
    """
    ...


def run_extraction(
    note_text: str,
    *,
    model: str = "deepseek-chat",
    base_url: str = "https://api.deepseek.com/v1",
    api_key: str | None = None,
    temperature: float = 0.0,
) -> ClinicalIntake:
    """Convenience: configure an LLM, build the chain, and extract.

    Args:
        note_text: Raw clinical note text.
        model: Model name (default deepseek-chat = deepseek-v3 on DeepSeek).
        base_url: API endpoint base URL.
        api_key: API key. Falls back to DEEPSEEK_API_KEY env var.
        temperature: LLM temperature (0.0 = deterministic).

    Returns:
        A ClinicalIntake instance with extracted fields.
    """
    ...
