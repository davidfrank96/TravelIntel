"""
Unit tests for InsightAnalyzer logic.
"""

from datetime import datetime, timedelta

from ai_predictor import InsightAnalyzer


def test_risk_grade_boundaries():
    ia = InsightAnalyzer()
    assert ia._risk_grade_from_score(1) == "A"
    assert ia._risk_grade_from_score(2) == "B"
    assert ia._risk_grade_from_score(3) == "C"
    assert ia._risk_grade_from_score(4) == "E"
    assert ia._risk_grade_from_score(1.5) == "B"
    assert ia._risk_grade_from_score(2.5) == "C"
    assert ia._risk_grade_from_score(3.5) == "D"
    assert ia._risk_grade_from_score(0) == "A"
    assert ia._risk_grade_from_score(5) == "E"
    assert ia._risk_grade_from_score(None) == "U"
    assert ia._risk_grade_from_score("foo") == "U"


def test_country_summary_uses_flags_and_recent_window():
    ia = InsightAnalyzer()
    now = datetime.utcnow()
    advisories = [
        {
            "country_normalized": "Kenya",
            "date": (now - timedelta(days=20)).isoformat(),
            "risk_score": 3,
            "description_cleaned": "Avoid protests and areas with crime.",
            "has_security_concerns": 1,
            "has_safety_concerns": 0,
            "has_serenity_concerns": 1,
            "corpus_risk_grade": "D",
        },
        {
            "country_normalized": "Kenya",
            "date": (now - timedelta(days=10)).isoformat(),
            "risk_score": 4,
            "description_cleaned": "You should register with local embassy.",
            "has_security_concerns": "true",
            "has_safety_concerns": "false",
            "has_serenity_concerns": "0",
            "corpus_risk_grade": "D",
        },
        # old row should be filtered out by default lookback
        {
            "country_normalized": "Kenya",
            "date": (now - timedelta(days=500)).isoformat(),
            "risk_score": 1,
            "description_cleaned": "Old advisory",
        },
    ]

    insight = ia.summarize_country(advisories, "Kenya")
    assert insight is not None
    assert insight.n_advisories == 2
    assert insight.has_security_issues is True
    assert insight.has_serenity_issues is True
    assert insight.risk_grade in {"C", "D", "E"}
    assert isinstance(insight.dos, list)
    assert isinstance(insight.donts, list)


def main():
    test_risk_grade_boundaries()
    test_country_summary_uses_flags_and_recent_window()
    print("insight analyzer tests passed")


if __name__ == "__main__":
    main()
