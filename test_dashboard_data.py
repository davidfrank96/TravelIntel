"""
Tests for dashboard data preparation utilities.
"""

import pandas as pd

from dashboard_utils import coerce_bool_series, ensure_analyzed_columns


def test_bool_coercion():
    s = pd.Series([True, False, 1, 0, "true", "false", "1", "0", None])
    out = coerce_bool_series(s).tolist()
    assert out == [True, False, True, False, True, False, True, False, False]


def test_ensure_analyzed_columns_from_raw_rows():
    df = pd.DataFrame(
        [
            {
                "source": "US State Department",
                "country": "Kenya",
                "risk_level": "Level 3 - Reconsider Travel",
                "description": "Crime and demonstrations may occur. You should carry ID.",
                "url": "https://example.com/kenya",
                "scraped_at": "2026-02-01T10:00:00",
            }
        ]
    )
    out = ensure_analyzed_columns(df)
    assert "country_normalized" in out.columns
    assert "risk_score" in out.columns
    assert "keywords" in out.columns
    assert "has_security_concerns" in out.columns
    assert out.loc[0, "country_normalized"] == "Kenya"
    assert int(out.loc[0, "risk_score"]) >= 3
    assert isinstance(out.loc[0, "keywords"], list)


def main():
    test_bool_coercion()
    test_ensure_analyzed_columns_from_raw_rows()
    print("dashboard data tests passed")


if __name__ == "__main__":
    main()
