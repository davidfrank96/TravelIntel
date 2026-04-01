"""PDF generation for TravelIntel briefings."""
from __future__ import annotations

from io import BytesIO
from typing import List

from fpdf import FPDF

from briefing.models import BriefingFull


class BriefingPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "TravelIntel Briefing", ln=True, align="C")
        self.ln(2)


def _section(pdf: FPDF, title: str, lines: List[str]):
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, title, ln=True)
    pdf.set_font("Helvetica", "", 11)
    for line in lines:
        if line:
            pdf.multi_cell(0, 6, f"- {line}")
    pdf.ln(1)


def generate_pdf(briefing: BriefingFull) -> bytes:
    pdf = BriefingPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    facts = briefing.facts
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"Risk Grade: {facts.risk_grade}")
    pdf.multi_cell(0, 6, facts.security_snapshot or "")
    pdf.ln(2)

    _section(
        pdf,
        "Emergency Numbers",
        [f"{n.label}: {n.number}" for n in facts.emergency_numbers],
    )
    _section(
        pdf,
        "Consulate",
        [
            f"{facts.consulate.name}",
            f"{facts.consulate.address}",
            f"{facts.consulate.phone}",
            f"{facts.consulate.website}",
        ],
    )
    _section(pdf, "Hospitals", [f"{h.name} - {h.address} {h.phone}" for h in facts.hospitals])
    _section(pdf, "Legal Restrictions", facts.legal_restrictions)
    _section(pdf, "Cultural Do's", facts.cultural_dos)
    _section(pdf, "Cultural Don'ts", facts.cultural_donts)
    _section(pdf, "Operational Guidance", facts.operational_guidance)
    _section(pdf, "Key Locations", facts.key_locations)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Narrative Briefing", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, briefing.narrative or "")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
