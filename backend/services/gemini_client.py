"""
Shared Gemini API Client — BrainBridge
=======================================
Barcha route'lar uchun yagona Gemini client.
- Async httpx (non-blocking)
- Retry logic (3 urinish)
- Structured logging
- Timeout boshqaruvi
"""
import os
import json
import re
import logging
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("brainbridge.gemini")

_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODELS = {
    "flash":      "gemini-2.0-flash",
    "flash_25":   "gemini-2.5-flash",
    "flash_lite": "gemini-2.0-flash-lite",
}

is_available = bool(_GEMINI_KEY)

if is_available:
    logger.info("[GeminiClient] Initialized ✓  model=gemini-2.0-flash")
else:
    logger.warning("[GeminiClient] GEMINI_API_KEY not set — AI features unavailable")


def _clean_json(raw: str) -> str:
    """Strip markdown fences and trailing commas from Gemini JSON output."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        raw = match.group(0)
    raw = re.sub(r"//[^\n\"]*\n", "\n", raw)
    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    return raw


async def generate_json(
    prompt: str,
    model: str = "flash",
    temperature: float = 0.3,
    max_tokens: int = 8192,
    response_schema: Optional[dict] = None,
    retries: int = 2,
) -> Optional[dict]:
    """
    Async JSON generation via Gemini.
    Returns parsed dict or None on failure.
    """
    if not is_available:
        logger.warning("[GeminiClient] API key not configured")
        return None

    model_name = MODELS.get(model, MODELS["flash"])
    endpoint = f"{_BASE_URL}/{model_name}:generateContent"

    gen_config: dict = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
        "candidateCount": 1,
        "responseMimeType": "application/json",
    }
    if response_schema:
        gen_config["responseSchema"] = response_schema

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }

    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                response = await client.post(
                    endpoint,
                    params={"key": _GEMINI_KEY},
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates in Gemini response")

            raw = candidates[0]["content"]["parts"][0].get("text", "")
            if not raw:
                raise ValueError("Empty text in Gemini response")

            cleaned = _clean_json(raw)
            result = json.loads(cleaned)
            logger.debug("[GeminiClient] Success  model=%s attempt=%d", model_name, attempt + 1)
            return result

        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            last_error = exc
            logger.warning(
                "[GeminiClient] HTTP error attempt=%d/%d: %s",
                attempt + 1, retries + 1, exc,
            )
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            last_error = exc
            logger.warning(
                "[GeminiClient] Parse error attempt=%d/%d: %s",
                attempt + 1, retries + 1, exc,
            )

    logger.error("[GeminiClient] All %d attempts failed: %s", retries + 1, last_error)
    return None


async def generate_text(
    prompt: str,
    history: Optional[list] = None,
    model: str = "flash_25",
    temperature: float = 0.6,
    max_tokens: int = 1200,
    system_prompt: Optional[str] = None,
    retries: int = 1,
) -> Optional[str]:
    """
    Async free-form text generation (for chat).
    Returns string or None on failure.
    """
    if not is_available:
        return None

    model_name = MODELS.get(model, MODELS["flash_25"])
    endpoint = f"{_BASE_URL}/{model_name}:generateContent"

    contents = []
    if system_prompt:
        contents.append({
            "role": "user",
            "parts": [{"text": system_prompt + "\n\n[Conversation starts]"}],
        })
        contents.append({
            "role": "model",
            "parts": [{"text": "Salom! Men BrainBot — ingliz tili o'qituvchingizman. Sizga qanday yordam bera olaman?"}],
        })

    for msg in (history or []):
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                response = await client.post(
                    endpoint,
                    params={"key": _GEMINI_KEY},
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()

            text = data["candidates"][0]["content"]["parts"][0].get("text", "").strip()
            if not text:
                raise ValueError("Empty text response")
            logger.debug("[GeminiClient] Chat success attempt=%d", attempt + 1)
            return text

        except Exception as exc:
            last_error = exc
            logger.warning("[GeminiClient] Chat error attempt=%d: %s", attempt + 1, exc)

    logger.error("[GeminiClient] Chat failed after %d attempts: %s", retries + 1, last_error)
    return None
