"""OpenAI client wrapper for TravelIntel briefings."""
import json
import os
from typing import Any, Dict, Optional

from openai import OpenAI

from briefing.prompts import FACTS_SYSTEM, FACTS_USER, NARRATIVE_SYSTEM, NARRATIVE_USER


class OpenAIBriefingClient:
    def __init__(self, model: Optional[str] = None):
        self.client = OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

    def _extract_text(self, response: Any) -> str:
        """Best-effort extraction of text from Responses API result."""
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text
        # Fallback for older SDK response shapes
        try:
            parts = []
            for item in response.output:
                for c in item.content:
                    if hasattr(c, "text") and c.text:
                        parts.append(c.text)
            return "\n".join(parts)
        except Exception:
            return ""

    def generate_facts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = FACTS_USER.format(**payload)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": FACTS_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        text = self._extract_text(response)
        try:
            return json.loads(text)
        except Exception:
            return {}

    def generate_narrative(self, payload: Dict[str, Any], facts_json: str) -> str:
        prompt = NARRATIVE_USER.format(**payload, facts_json=facts_json)
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": NARRATIVE_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        return self._extract_text(response).strip()
