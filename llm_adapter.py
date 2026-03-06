import os
from typing import Tuple, Dict, Any

# Only OpenAI implemented for now.
# Future providers can be added behind the same interface.

def llm_complete(
    messages: list,
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> Tuple[str, Dict[str, Any]]:
    """
    Minimal abstraction layer for LLM calls.

    Returns:
        text: str
        meta: dict (provider, model, token usage if available)
    """

    provider = os.getenv("VAL0_LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return _openai_complete(messages, temperature, max_tokens)

    raise RuntimeError(f"Unsupported LLM provider: {provider}")


def _openai_complete(messages, temperature, max_tokens):
    """
    OpenAI implementation.
    Keeps behavior identical to current direct call.
    """

    from openai import OpenAI

    client = OpenAI()

    model = os.getenv("VAL0_OPENAI_MODEL", "gpt-4o-mini")

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    text = resp.choices[0].message.content

    meta = {
        "provider": "openai",
        "model": model,
        "usage": getattr(resp, "usage", None),
    }

    return text, meta
