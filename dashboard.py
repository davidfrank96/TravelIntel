"""
Streamlit dashboard for Travel Security / Safety insights.

Run with:
    streamlit run dashboard.py
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from ai_predictor import InsightAnalyzer
from dashboard_utils import add_reason_columns, coerce_bool_series, ensure_analyzed_columns
from db_factory import get_handler


st.set_page_config(page_title="Travel Security Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_data(country_filter=None, source_filter=None, days_back: int = 365):
    db = get_handler()
    try:
        advisories = db.get_advisories(
            country=country_filter,
            source=source_filter,
            limit=5000,
        )
    finally:
        db.close()

    if not advisories:
        return pd.DataFrame()

    df = pd.DataFrame(advisories)
    df = ensure_analyzed_columns(df)
    df = add_reason_columns(df)

    if "date" in df.columns and "scraped_at" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
        df["date"] = df["date"].fillna(df["scraped_at"])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    cutoff = datetime.utcnow() - timedelta(days=days_back)
    df = df.dropna(subset=["date"])
    df = df[df["date"] >= cutoff]
    return df


def summarize_location(df_country: pd.DataFrame) -> str:
    if df_country.empty:
        return "No recent advisories for this location."

    meaningful = (
        df_country[df_country.get("description_cleaned", pd.Series(dtype=str)).fillna("").str.strip().str.len() >= 40]
        if "description_cleaned" in df_country.columns
        else df_country
    )
    if meaningful.empty and "description" in df_country.columns:
        meaningful = df_country[df_country["description"].fillna("").str.strip().str.len() >= 40]
    if meaningful.empty:
        return (
            "No detailed advisory text found for this location yet. "
            "Try re-running the scraper to pull full country advisory pages."
        )

    analyzer = InsightAnalyzer()
    records = meaningful.to_dict(orient="records")
    example_country = meaningful["country_normalized"].iloc[0]
    insight = analyzer.summarize_country(records, example_country)
    if not insight:
        return "No recent advisories for this location."

    parts = []
    grade = insight.risk_grade or "U"
    parts.append(f"Overall risk rating: **{grade}** ({insight.risk_level_text}).")

    if insight.has_security_issues:
        parts.append("**Security** issues reported (crime / terrorism / unrest).")
    if insight.has_safety_issues:
        parts.append("**Safety** issues reported (health / disasters / accidents).")
    if insight.has_serenity_issues:
        parts.append("**Serenity** impacted (protests / strikes / political tension).")
    if (
        not insight.has_security_issues
        and not insight.has_safety_issues
        and not insight.has_serenity_issues
    ):
        parts.append("No major security / safety / serenity issues explicitly mentioned in recent advisories.")

    if "risk_reason" in meaningful.columns:
        reason_rows = meaningful[meaningful["risk_reason"].fillna("").str.strip().str.len() > 0]
    else:
        reason_rows = pd.DataFrame()

    if not reason_rows.empty:
        latest_reason = reason_rows.sort_values("date", ascending=False).iloc[0]
        top_reason = latest_reason.get("risk_reason", "")
        top_keywords = latest_reason.get("risk_keywords", "")
        if top_reason:
            parts.append(f"**Why unsafe:** {top_reason}")
        if top_keywords:
            parts.append(f"**Key risk keywords:** {top_keywords}")
    elif insight.latest_summary and insight.risk_grade in {"C", "D", "E"}:
        parts.append(f'Latest signal: "{insight.latest_summary}"')

    if insight.security_highlights:
        parts.append("\n**Key security highlights:**")
        for h in insight.security_highlights:
            parts.append(f"- {h}")

    if insight.dos:
        parts.append("\n**Do's (recommended actions):**")
        for d in insight.dos:
            parts.append(f"- {d}")

    if insight.donts:
        parts.append("\n**Don'ts (what to avoid):**")
        for d in insight.donts:
            parts.append(f"- {d}")

    return "\n".join(parts)


def main():
    st.title("Travel Security & Safety Dashboard")
    st.sidebar.header("Filters")

    country_input = st.sidebar.text_input("Country (optional, partial name allowed)", value="")
    source_input = st.sidebar.selectbox(
        "Source",
        options=[
            "All",
            "US State Department",
            "UK FCDO",
            "Smart Traveller (Australia)",
            "IATA Travel Centre",
            "Canada Travel",
        ],
    )
    days_back = st.sidebar.slider("Look back (days)", min_value=30, max_value=730, value=365, step=30)

    source_filter = None if source_input == "All" else source_input
    country_filter = country_input if country_input.strip() else None
    df = load_data(country_filter=country_filter, source_filter=source_filter, days_back=days_back)

    if df.empty:
        st.info("No advisories found for the selected filters.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Advisories (filtered)", len(df))
    with col2:
        n_high = (df.get("risk_score", 0) >= 3).sum()
        st.metric("High/Very High Risk", int(n_high))
    with col3:
        st.metric("Countries covered", df["country_normalized"].nunique())
    with col4:
        latest_date = df["date"].max()
        st.metric("Last updated", latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "N/A")

    st.subheader("Location insights")
    all_countries = sorted(df["country_normalized"].dropna().unique())
    default_country = all_countries[0] if all_countries else None
    country_focus = st.selectbox(
        "Focus country",
        options=all_countries,
        index=all_countries.index(default_country) if default_country in all_countries else 0,
    )

    df_country = df[df["country_normalized"] == country_focus]
    st.markdown(f"### {country_focus}: Risk Rating & Guidance")
    st.markdown(summarize_location(df_country))

    st.markdown("### Concern Categories (this country)")
    col1, col2, col3 = st.columns(3)
    with col1:
        sec_count = int(coerce_bool_series(df_country["has_security_concerns"]).sum())
        st.metric("Security Concerns", sec_count)
    with col2:
        safe_count = int(coerce_bool_series(df_country["has_safety_concerns"]).sum())
        st.metric("Safety Concerns", safe_count)
    with col3:
        ser_count = int(coerce_bool_series(df_country["has_serenity_concerns"]).sum())
        st.metric("Serenity Concerns", ser_count)

    st.markdown("### Risk level distribution (this country)")
    if "risk_level_normalized" in df_country.columns:
        st.bar_chart(df_country["risk_level_normalized"].value_counts().sort_index())

    st.markdown("### Top Keywords (this country)")
    all_keywords = []
    for keywords_list in df_country.get("keywords", []):
        if isinstance(keywords_list, list):
            all_keywords.extend(keywords_list)
    if all_keywords:
        keyword_counts = pd.Series(all_keywords).value_counts().head(15)
        st.bar_chart(keyword_counts)
    else:
        st.info("No keywords extracted yet.")

    st.markdown("### Recent advisories (this country)")
    cols_to_show = [
        "source",
        "risk_level_normalized",
        "risk_score",
        "corpus_risk_grade",
        "date",
        "risk_keywords",
        "risk_reason",
        "has_security_concerns",
        "has_safety_concerns",
        "has_serenity_concerns",
    ]
    cols_existing = [c for c in cols_to_show if c in df_country.columns]
    display_df = df_country[cols_existing].sort_values("date", ascending=False).reset_index(drop=True)

    for col in ["has_security_concerns", "has_safety_concerns", "has_serenity_concerns"]:
        if col in display_df.columns:
            display_df[col] = coerce_bool_series(display_df[col]).apply(lambda x: "Yes" if x else "No")

    st.dataframe(display_df, use_container_width=True, height=400)

    st.markdown("### Global risk by country (filtered dataset)")
    if "risk_score" in df.columns:
        country_risk = (
            df.groupby("country_normalized")["risk_score"].mean().sort_values(ascending=False).reset_index()
        )
        st.bar_chart(country_risk.set_index("country_normalized"))

    st.markdown("### Global Concern Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        sec_global = int(coerce_bool_series(df["has_security_concerns"]).sum())
        pct_sec = (sec_global / len(df) * 100) if len(df) > 0 else 0
        st.metric("Security Issues (%)", f"{pct_sec:.1f}%")
    with col2:
        safe_global = int(coerce_bool_series(df["has_safety_concerns"]).sum())
        pct_safe = (safe_global / len(df) * 100) if len(df) > 0 else 0
        st.metric("Safety Issues (%)", f"{pct_safe:.1f}%")
    with col3:
        ser_global = int(coerce_bool_series(df["has_serenity_concerns"]).sum())
        pct_ser = (ser_global / len(df) * 100) if len(df) > 0 else 0
        st.metric("Serenity Issues (%)", f"{pct_ser:.1f}%")


if __name__ == "__main__":
    main()
