"""
Utilities for dashboard data preparation and robust metric computation.
"""

import json
import re
from typing import Any

import pandas as pd


TRUE_STRINGS = {"1", "true", "t", "yes", "y"}
FALSE_STRINGS = {"0", "false", "f", "no", "n", ""}

RISK_TERMS = [
    "terrorism", "terrorist", "attack", "armed conflict", "war", "civil war",
    "kidnap", "kidnapping", "hostage", "crime", "violent crime", "robbery",
    "carjacking", "assault", "murder", "gang", "cartel", "bombing", "shooting",
    "protest", "demonstration", "riot", "civil unrest", "strike", "instability",
    "political tension", "health risk", "disease", "epidemic", "pandemic",
    "cholera", "dengue", "malaria", "earthquake", "flood", "hurricane", "wildfire",
]

NOISE_PATTERNS = [
    r"^download a more detailed map.*?(?=\.)\.?",
    r"^no travel can be guaranteed safe.*?(?=\.)\.?",
    r"^read all the advice in this guide.*?(?=\.)\.?",
    r"^the british antarctic territory.*?(?=\.)\.?",
    r"^the .* website has more information.*?(?=\.)\.?",
]


def coerce_bool(value: Any) -> bool:
    """Convert mixed bool-like values safely."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        low = value.strip().lower()
        if low in TRUE_STRINGS:
            return True
        if low in FALSE_STRINGS:
            return False
    return bool(value)


def coerce_bool_series(series: pd.Series) -> pd.Series:
    """Vectorized boolean coercion for dashboard counts."""
    return series.apply(coerce_bool)


def _normalize_keywords(value: Any):
    """Normalize keywords column values into a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v).strip()]
        except Exception:
            pass
        # fallback: comma-separated keywords
        return [v.strip() for v in raw.split(",") if v.strip()]
    return []


def ensure_analyzed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure cleaned/analyzed columns exist for dashboard rendering.
    If missing, derive them from raw fields using DataCleaner.
    """
    if df.empty:
        return df

    out = df.copy()
    required_cols = [
        "country_normalized",
        "risk_level_normalized",
        "risk_score",
        "description_cleaned",
        "keywords",
        "sentiment_score",
        "has_security_concerns",
        "has_safety_concerns",
        "has_serenity_concerns",
        "corpus_risk_grade",
    ]

    def _is_missing(v: Any) -> bool:
        if v is None:
            return True
        if isinstance(v, list):
            return len(v) == 0
        if isinstance(v, str) and not v.strip():
            return True
        try:
            if pd.isna(v):
                return True
        except Exception:
            return False
        if isinstance(v, float) and pd.isna(v):
            return True
        return False

    cleaner = None
    try:
        from data_cleaner import DataCleaner

        cleaner = DataCleaner()
    except Exception:
        cleaner = None

    enriched = []
    for rec in out.to_dict(orient="records"):
        need_row_enrichment = any(
            (col not in rec) or _is_missing(rec.get(col))
            for col in required_cols
            if col not in {"has_security_concerns", "has_safety_concerns", "has_serenity_concerns", "keywords"}
        )

        if need_row_enrichment:
            if cleaner is not None:
                cleaned = cleaner.clean_advisory(rec)
            else:
                # Minimal fallback enrichment when NLP dependencies are unavailable.
                risk_raw = str(rec.get("risk_level") or "").lower()
                if "level 4" in risk_raw or "do not travel" in risk_raw:
                    risk_score = 4
                    risk_norm = "Do Not Travel"
                elif "level 3" in risk_raw or "reconsider" in risk_raw:
                    risk_score = 3
                    risk_norm = "Reconsider Travel"
                elif "level 2" in risk_raw or "exercise increased" in risk_raw:
                    risk_score = 2
                    risk_norm = "Exercise Increased Caution"
                elif "level 1" in risk_raw or "low" in risk_raw:
                    risk_score = 1
                    risk_norm = "Low Risk"
                else:
                    risk_score = 0
                    risk_norm = rec.get("risk_level")

                desc = str(rec.get("description") or "")
                low = desc.lower()
                cleaned = {
                    "country_normalized": str(rec.get("country") or "Unknown").title(),
                    "risk_level_normalized": risk_norm,
                    "risk_score": risk_score,
                    "description_cleaned": desc.strip(),
                    "keywords": [],
                    "sentiment_score": 0.0,
                    "has_security_concerns": any(t in low for t in ["crime", "terror", "attack", "violence"]),
                    "has_safety_concerns": any(t in low for t in ["health", "disease", "flood", "earthquake"]),
                    "has_serenity_concerns": any(t in low for t in ["protest", "unrest", "strike", "riot"]),
                    "corpus_risk_grade": "A",
                    "date_parsed": None,
                }
            merged = rec.copy()
            for col in required_cols:
                val = rec.get(col)
                merged[col] = cleaned.get(col) if _is_missing(val) else val
            if not merged.get("date"):
                merged["date"] = cleaned.get("date_parsed") or rec.get("scraped_at")
            enriched.append(merged)
        else:
            enriched.append(rec)
    out = pd.DataFrame(enriched)

    if "keywords" in out.columns:
        out["keywords"] = out["keywords"].apply(_normalize_keywords)

    # force boolean columns to true booleans for consistent metrics
    for col in ["has_security_concerns", "has_safety_concerns", "has_serenity_concerns"]:
        if col in out.columns:
            out[col] = coerce_bool_series(out[col])

    return out


def _clean_reason_text(text: str) -> str:
    out = (text or "").strip()
    if not out:
        return ""
    for pat in NOISE_PATTERNS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE).strip()
    out = re.sub(r"\s+", " ", out).strip()
    return out


def _extract_reason_and_keywords(text: str):
    cleaned = _clean_reason_text(text)
    if not cleaned:
        return "", []

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
    matched_terms = []
    reason_sentences = []
    for s in sentences:
        low = s.lower()
        sentence_terms = [t for t in RISK_TERMS if t in low]
        if sentence_terms:
            matched_terms.extend(sentence_terms)
            reason_sentences.append(s)

    # Deduplicate preserving order.
    seen = set()
    keywords = []
    for t in matched_terms:
        if t not in seen:
            seen.add(t)
            keywords.append(t)

    if reason_sentences:
        reason = " ".join(reason_sentences[:2])
    else:
        # No hazard terms found -> do not return generic boilerplate.
        reason = ""
    return reason, keywords[:8]


def add_reason_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add human-readable risk reason and extracted risk keywords per advisory row."""
    if df.empty:
        return df
    out = df.copy()
    reasons = []
    kw_joined = []
    for rec in out.to_dict(orient="records"):
        text = rec.get("description_cleaned") or rec.get("description") or ""
        reason, kws = _extract_reason_and_keywords(str(text))
        reasons.append(reason)
        kw_joined.append(", ".join(kws))
    out["risk_reason"] = reasons
    out["risk_keywords"] = kw_joined
    return out
