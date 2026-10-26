"""Unified LLM client interface supporting Gemini, Anthropic, OpenAI/Groq, and simulation."""

import json
import logging
import re
import os
from typing import Dict, Any, Optional
from src.config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_MODEL,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and parse JSON safely."""
    text = raw_text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract content within ```json ... ``` or ``` ... ``` code fence
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        fence_content = fence_match.group(1).strip()
        try:
            return json.loads(fence_content)
        except json.JSONDecodeError:
            text = fence_content  # Fall through to brace extraction on fence content

    # 3. Robust substring extraction: outermost { to outermost }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    # 4. Fallback for array root if applicable
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        try:
            return json.loads(text[first_bracket : last_bracket + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse LLM response as JSON. Output was:\n{raw_text}")


class LLMClient:
    """Unified LLM caller that routes to Gemini, Anthropic, or OpenAI/Groq."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER).lower()
        self.gemini_client = None
        self.anthropic_client = None
        self.openai_client = None

        # 1. Google Gemini (Ideal for free prototype)
        if GEMINI_API_KEY and self.provider in ("gemini", "auto"):
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                self.provider = "gemini"
            except ImportError:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                    self.provider = "gemini"
                except Exception as e:
                    logger.warning(f"Could not initialize Gemini: {e}")
            except Exception as e:
                logger.warning(f"Could not initialize google-genai Client: {e}")

        # 2. Anthropic Claude
        if not self.gemini_client and ANTHROPIC_API_KEY and self.provider in ("anthropic", "auto"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic: {e}")

        # 3. OpenAI / Groq Compatible
        if not self.gemini_client and not self.anthropic_client and OPENAI_API_KEY and self.provider in ("openai", "groq", "auto"):
            try:
                import openai
                base_url = os.getenv("OPENAI_BASE_URL", None)  # Allows Groq endpoint: https://api.groq.com/openai/v1
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=base_url)
                self.provider = "openai"
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI/Groq: {e}")

        if not any([self.gemini_client, self.anthropic_client, self.openai_client]):
            if self.provider != "simulation":
                logger.info("No active API keys found; activating smart simulation generator.")
            self.provider = "simulation"

    def generate_json(
        self, system_prompt: str, user_prompt: str, default_fallback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Invoke LLM and return parsed JSON object."""
        if self.provider == "gemini" and self.gemini_client:
            try:
                combined_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}\n\nOutput strictly valid JSON only."
                if hasattr(self.gemini_client, "models"):  # google-genai SDK
                    model_name = GEMINI_MODEL or "gemini-1.5-flash"
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=combined_prompt,
                    )
                    return clean_json_response(response.text)
                else:  # google.generativeai legacy SDK
                    response = self.gemini_client.generate_content(combined_prompt)
                    return clean_json_response(response.text)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    logger.warning("Gemini Free Tier daily limit reached (20 req/day). Using calibrated generator fallback.")
                elif "503" in err_str or "UNAVAILABLE" in err_str:
                    logger.warning("Gemini model temporarily busy (503). Using calibrated generator fallback.")
                else:
                    logger.error(f"Gemini API call failed: {e}")

                if default_fallback:
                    return default_fallback
                raise

        elif self.provider == "anthropic" and self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=2500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return clean_json_response(response.content[0].text)
            except Exception as e:
                logger.error(f"Anthropic API call failed: {e}")
                if default_fallback:
                    return default_fallback
                raise

        elif self.provider in ("openai", "groq") and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return clean_json_response(response.choices[0].message.content)
            except Exception as e:
                logger.error(f"OpenAI/Groq API call failed: {e}")
                if default_fallback:
                    return default_fallback
                raise

        elif self.provider == "simulation":
            if default_fallback:
                return default_fallback
            raise RuntimeError("Simulation provider requested but no fallback handler was provided.")

        raise RuntimeError(f"Unsupported or unconfigured LLM provider: {self.provider}")
