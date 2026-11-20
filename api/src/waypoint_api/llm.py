"""Call the language model (Anthropic Claude).

The model and effort come from WAYPOINT_LLM_MODEL and WAYPOINT_LLM_EFFORT,
so candidates can be compared without code changes (see plan 03).
"""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
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
# Yields the answer's text as it is generated, then the finished Reply.
Stream = Callable[[str, list[dict]], Iterator[str | Reply]]


def request(system: str, messages: list[dict]) -> dict:
    """The request options shared by complete and stream. The system prompt
    is marked for caching; server-side fallback retries declines it can serve
    on another model."""
    return {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ],
        "messages": messages,
        "output_config": {"effort": EFFORT},
        "betas": [FALLBACK_BETA],
        "fallbacks": "default",
    }


@contextmanager
def api_errors() -> Iterator[None]:
    """Turn API failures into LLMError with a message fit for a student."""
    try:
        yield
    except anthropic.RateLimitError as error:
        raise LLMError("The language model is busy. Try again shortly.") from error
    except anthropic.APITimeoutError as error:
        raise LLMError("The language model timed out.") from error
    except anthropic.APIConnectionError as error:
        raise LLMError("Could not reach the language model.") from error
    except anthropic.APIStatusError as error:
        raise LLMError(f"The language model failed ({error.status_code}).") from error


def client() -> anthropic.Anthropic:
    """An API client with the instructor's timeout."""
    return anthropic.Anthropic(timeout=TIMEOUT_S)


def complete(system: str, messages: list[dict]) -> Reply:
    """Ask the model for one complete answer. Refusals, truncated answers and
    API failures raise LLMError, so no partial answer is passed off as whole."""
    with api_errors():
        response = client().beta.messages.create(**request(system, messages))
    return reply_from(response)


def stream(system: str, messages: list[dict]) -> Iterator[str | Reply]:
    """Yield the answer's text as it arrives, then the finished Reply.

    Errors raise LLMError, even after some text was sent: the caller must
    treat text without a final Reply as incomplete. After a server-side
    fallback the new model continues the text already sent.
    """
    with api_errors(), client().beta.messages.stream(**request(system, messages)) as s:
        yield from s.text_stream
        final = s.get_final_message()
    yield reply_from(final)


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
