"""Call the language model (Anthropic Claude).

The model and effort come from WAYPOINT_LLM_MODEL and WAYPOINT_LLM_EFFORT,
so candidates can be compared without code changes (see plan 03).
"""

import os
from collections.abc import Callable
from dataclasses import dataclass

import anthropic

MODEL = os.environ.get("WAYPOINT_LLM_MODEL", "claude-sonnet-5-5")
EFFORT = os.environ.get("WAYPOINT_LLM_EFFORT", "low")
MAX_TOKENS = 8000
TIMEOUT_S = 120.0
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMError(Exception):
    """The model could not give a complete answer."""


@dataclass
class Reply:
    """A complete model answer and what it cost."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


Complete = Callable[[str, list[dict]], Reply]


def complete(system: str, messages: list[dict]) -> Reply:
    """Ask the model for one complete answer.

    The system prompt is marked for caching. Server-side fallback retries
    declines it can serve on another model. Refusals, truncated answers and
    API failures raise LLMError, so no partial answer is passed off as whole.
    """
    try:
        response = anthropic.Anthropic(timeout=TIMEOUT_S).beta.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ],
            messages=messages,
            output_config={"effort": EFFORT},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except anthropic.RateLimitError as error:
        raise LLMError("The language model is busy. Try again shortly.") from error
    except anthropic.APITimeoutError as error:
        raise LLMError("The language model timed out.") from error
    except anthropic.APIConnectionError as error:
        raise LLMError("Could not reach the language model.") from error
    except anthropic.APIStatusError as error:
        raise LLMError(f"The language model failed ({error.status_code}).") from error
    return reply_from(response)


def reply_from(response) -> Reply:
    """Accept only a finished answer."""
    if response.stop_reason == "refusal":
        raise LLMError("The language model declined to answer.")
    if response.stop_reason != "end_turn":
        raise LLMError(f"The answer was incomplete ({response.stop_reason}).")
    text = "".join(block.text for block in response.content if block.type == "text")
    usage = response.usage
    return Reply(
        text,
        response.model,
        usage.input_tokens,
        usage.output_tokens,
        usage.cache_read_input_tokens or 0,
        usage.cache_creation_input_tokens or 0,
    )
