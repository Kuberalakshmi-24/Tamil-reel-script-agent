"""Unified LLM client interface supporting Anthropic, OpenAI, and simulation mode."""

import json
import logging
import re
from typing import Dict, Any, Optional
from src.config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and parse JSON safely."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try extracting JSON object substring
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse LLM response as JSON: {e}\nRaw text:\n{raw_text}")


class LLMClient:
    """Unified LLM caller that routes to Anthropic, OpenAI, or smart simulation."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER).lower()
        self.anthropic_client = None
        self.openai_client = None

        if ANTHROPIC_API_KEY and self.provider in ("anthropic", "auto"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

        if not self.anthropic_client and OPENAI_API_KEY and self.provider in ("openai", "auto"):
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
                self.provider = "openai"
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

        if not self.anthropic_client and not self.openai_client:
            if self.provider != "simulation":
                logger.info("No active API keys found; activating smart simulation generator.")
            self.provider = "simulation"

    def generate_json(self, system_prompt: str, user_prompt: str, default_fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke LLM and return parsed JSON object."""
        if self.provider == "anthropic" and self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=2500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw_text = response.content[0].text
                return clean_json_response(raw_text)
            except Exception as e:
                logger.error(f"Anthropic API call failed: {e}")
                if default_fallback:
                    return default_fallback
                raise

        elif self.provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                raw_text = response.choices[0].message.content
                return clean_json_response(raw_text)
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}")
                if default_fallback:
                    return default_fallback
                raise

        elif self.provider == "simulation":
            if default_fallback:
                return default_fallback
            raise RuntimeError("Simulation provider requested but no fallback handler was provided.")

        raise RuntimeError(f"Unsupported or unconfigured LLM provider: {self.provider}")
