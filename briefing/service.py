"""Core business logic for generating and caching TravelIntel briefings."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from briefing.models import BriefingFacts, BriefingFull, BriefingPreview
from briefing.openai_client import OpenAIBriefingClient
from briefing.store import BriefingStore


class BriefingService:
    def __init__(self):
        self.cache_days = int(os.getenv("BRIEFING_CACHE_DAYS", "7"))
        self.store = BriefingStore()
        self.llm = OpenAIBriefingClient()

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure consistent formatting for cache keys
        cleaned = dict(payload)
        cleaned["nationality"] = cleaned.get("nationality", "").strip()
        cleaned["destination_country"] = cleaned.get("destination_country", "").strip()
        cleaned["destination_city"] = cleaned.get("destination_city", "").strip()
        cleaned["trip_type"] = cleaned.get("trip_type", "").strip()
        return cleaned

    def _facts_from_row(self, row: Dict[str, Any]) -> BriefingFacts:
        raw = row.get("facts_json") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = {}
        return BriefingFacts(**raw)

    def _preview_from_row(self, row: Dict[str, Any], cached: bool) -> BriefingPreview:
        facts = self._facts_from_row(row)
        return BriefingPreview(
            briefing_id=str(row.get("briefing_id")),
            risk_grade=row.get("risk_grade") or facts.risk_grade,
            security_snapshot=row.get("security_snapshot") or facts.security_snapshot,
            emergency_numbers=facts.emergency_numbers,
            cached=cached,
            created_at=row.get("created_at") or datetime.utcnow(),
        )

    def _full_from_row(self, row: Dict[str, Any], cached: bool) -> BriefingFull:
        facts = self._facts_from_row(row)
        return BriefingFull(
            briefing_id=str(row.get("briefing_id")),
            facts=facts,
            narrative=row.get("narrative") or "",
            cached=cached,
            created_at=row.get("created_at") or datetime.utcnow(),
            paid=row.get("paid_at") is not None,
        )

    def get_preview(self, payload: Dict[str, Any]) -> BriefingPreview:
        payload = self._normalize_payload(payload)
        cached = self.store.get_cached(
            payload["nationality"],
            payload["destination_country"],
            payload["destination_city"],
            payload["trip_type"],
            self.cache_days,
        )
        if cached:
            return self._preview_from_row(cached, cached=True)

        facts = self.llm.generate_facts(payload)
        facts_obj = BriefingFacts(**facts) if facts else BriefingFacts()
        narrative = self.llm.generate_narrative(payload, json.dumps(facts_obj.dict()))

        row = self.store.save_briefing(
            payload=payload,
            facts=facts_obj.dict(),
            narrative=narrative,
            risk_grade=facts_obj.risk_grade,
            security_snapshot=facts_obj.security_snapshot,
            emergency_numbers=[n.dict() for n in facts_obj.emergency_numbers],
        )
        return self._preview_from_row(row, cached=False)

    def get_full(self, payload: Dict[str, Any], mark_paid: bool, payment_reference: Optional[str] = None) -> BriefingFull:
        payload = self._normalize_payload(payload)
        cached = self.store.get_cached(
            payload["nationality"],
            payload["destination_country"],
            payload["destination_city"],
            payload["trip_type"],
            self.cache_days,
        )
        if cached:
            if mark_paid:
                self.store.mark_paid(str(cached.get("briefing_id")), payment_reference)
                cached = self.store.get_briefing(str(cached.get("briefing_id"))) or cached
            return self._full_from_row(cached, cached=True)

        facts = self.llm.generate_facts(payload)
        facts_obj = BriefingFacts(**facts) if facts else BriefingFacts()
        narrative = self.llm.generate_narrative(payload, json.dumps(facts_obj.dict()))

        row = self.store.save_briefing(
            payload=payload,
            facts=facts_obj.dict(),
            narrative=narrative,
            risk_grade=facts_obj.risk_grade,
            security_snapshot=facts_obj.security_snapshot,
            emergency_numbers=[n.dict() for n in facts_obj.emergency_numbers],
        )
        if mark_paid:
            self.store.mark_paid(str(row.get("briefing_id")), payment_reference)
            row = self.store.get_briefing(str(row.get("briefing_id"))) or row
        return self._full_from_row(row, cached=False)
