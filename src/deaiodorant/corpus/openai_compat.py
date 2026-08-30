"""Shared helpers for auditable OpenAI-compatible structured responses."""

from __future__ import annotations

from typing import Any


REASONING_MODES = ("legacy", "disabled", "low", "medium", "high")


def reasoning_parameters(mode: str) -> dict[str, Any]:
    """Return explicit reasoning controls without assuming provider defaults."""

    if mode not in REASONING_MODES:
        raise ValueError(f"Unknown OpenAI-compatible reasoning mode: {mode}")
    if mode == "legacy":
        return {"chat_template_kwargs": {"enable_thinking": False}}
    if mode == "disabled":
        return {"reasoning": {"enabled": False}}
    return {"reasoning": {"effort": mode, "exclude": False}}


def extract_answer_text(response_payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Extract text and non-sensitive diagnostics from a chat completion."""

    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return "", {"failure": "missing_choices"}
    choice = choices[0]
    if not isinstance(choice, dict):
        return "", {"failure": "invalid_choice"}
    message = choice.get("message")
    if not isinstance(message, dict):
        return "", {"failure": "missing_message"}

    content = message.get("content")
    parts: list[str] = []
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, dict):
        value = content.get("text", content.get("content"))
        if isinstance(value, str):
            parts.append(value)
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                value = part.get("text", part.get("content"))
                if isinstance(value, str):
                    parts.append(value)
    text = "".join(parts)

    usage = response_payload.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    completion_details = usage.get("completion_tokens_details")
    completion_details = (
        completion_details if isinstance(completion_details, dict) else {}
    )
    reasoning = message.get("reasoning")
    diagnostics = {
        "response_model": response_payload.get("model"),
        "provider": response_payload.get("provider"),
        "finish_reason": choice.get("finish_reason"),
        "native_finish_reason": choice.get("native_finish_reason"),
        "content_type": type(content).__name__,
        "content_chars": len(text),
        "reasoning_chars": len(reasoning) if isinstance(reasoning, str) else 0,
        "reasoning_detail_count": (
            len(message["reasoning_details"])
            if isinstance(message.get("reasoning_details"), list)
            else 0
        ),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": completion_details.get("reasoning_tokens"),
    }
    if not text.strip():
        diagnostics["failure"] = "empty_answer_content"
    return text, diagnostics


def format_response_failure(diagnostics: dict[str, Any]) -> str:
    """Format bounded diagnostics suitable for a fail-closed evidence field."""

    failure = diagnostics.get("failure") or "invalid_content"
    finish = diagnostics.get("finish_reason") or "unknown"
    return f"Response failed: {failure}/{finish}."
