"""
LangChain extraction pipeline — prompt → LLM → Pydantic parser.

Builds an LCEL chain that takes a raw note text, sends it through the
prompt template to DeepSeek (openai-compatible API), and parses the
output into a ClinicalIntake Pydantic model.

Exports:
    build_chain: Factory that constructs the pipeline given an LLM instance.
    run_extraction: Convenience function: LLM setup → chain → result.
"""

import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable

from clinical_intake.schemas import ClinicalIntake
from clinical_intake.prompts import SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE


def build_chain(llm: ChatOpenAI) -> Runnable:
    """Construct the extraction chain: prompt template → LLM → parser.
    LLM returns raw JSON string through prompts, 
    Parser extracts JSON and validates, then parses into ClinicalIntake object

    Args:
        llm: A configured ChatOpenAI instance (pointed at DeepSeek).

    Returns:
        An LCEL Runnable that accepts a dict with a "note_text" key
        and returns a ClinicalIntake instance.
    """
    parser = PydanticOutputParser(pydantic_object=ClinicalIntake)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT_TEMPLATE),
    ])
    
    # Lock format_instructions into the prompt at build time
    # so they don't have to be passed on every invocation
    prompt_with_instructions = prompt.partial(
        format_instructions=parser.get_format_instructions()
    )
    
    chain = prompt_with_instructions | llm | parser
    return chain


def run_extraction(
    note_text: str,
    *,
    model: str = "deepseek-v4-flash",
    base_url: str = "https://api.deepseek.com",
    api_key: str | None = None,
    temperature: float = 0.0,
) -> ClinicalIntake:
    """Convenience: configure an LLM, build the chain, and extract.

    Args:
        note_text: Raw clinical note text.
        model: Model name (default deepseek-v4-flash on DeepSeek).
        base_url: API endpoint base URL.
        api_key: API key. Falls back to DEEPSEEK_API_KEY env var.
        temperature: LLM temperature (0.0 = deterministic).

    Returns:
        A ClinicalIntake instance with extracted fields.
    """
    resolved_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not resolved_key:
        raise ValueError(
            "DEEPSEEK_API_KEY not set. Provide api_key or set the DEEPSEEK_API_KEY environment variable."
        )

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=resolved_key,
        temperature=temperature,
    )

    chain = build_chain(llm)
    result = chain.invoke({"note_text": note_text})
    return result
