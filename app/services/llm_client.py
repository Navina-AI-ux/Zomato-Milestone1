from __future__ import annotations

import logging
import time
from typing import Any

from groq import Groq, APIStatusError, APITimeoutError

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client(api_key: str) -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=api_key)
    return _client


def chat_complete(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    timeout: float = 30.0,
) -> str:
    """
    Call Groq chat completions and return the raw response text.

    Retries once on transient errors (timeout / 5xx).
    Raises on the second failure so the caller can activate the fallback path.
    """
    client = _get_client(api_key)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in (1, 2):
        try:
            t0 = time.monotonic()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                response_format={"type": "json_object"},
            )
            latency = time.monotonic() - t0
            logger.info("Groq response received (attempt %d, %.2fs).", attempt, latency)
            return response.choices[0].message.content or ""

        except APITimeoutError as exc:
            logger.warning("Groq timeout on attempt %d: %s", attempt, exc)
            if attempt == 2:
                raise

        except APIStatusError as exc:
            # Retry only on server-side errors (5xx)
            if exc.status_code >= 500:
                logger.warning(
                    "Groq server error %d on attempt %d: %s",
                    exc.status_code,
                    attempt,
                    exc.message,
                )
                if attempt == 2:
                    raise
            else:
                # 4xx errors are not retryable
                raise
