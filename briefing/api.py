"""FastAPI entrypoint for TravelIntel briefing service."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse

from briefing.models import BriefingRequest, BriefingFullRequest
from briefing.service import BriefingService
from briefing.pdf import generate_pdf

app = FastAPI(title="TravelIntel Briefing API")
service = BriefingService()


@app.post("/briefings/preview")
def create_preview(request: BriefingRequest):
    preview = service.get_preview(request.dict())
    return preview


@app.post("/briefings/full")
def create_full(request: BriefingFullRequest):
    if not request.paid:
        preview = service.get_preview(request.dict())
        return JSONResponse(status_code=402, content={
            "message": "Payment required to unlock full briefing.",
            "preview": preview.dict(),
        })

    full = service.get_full(
        request.dict(),
        mark_paid=True,
        payment_reference=request.payment_reference,
    )
    return full


@app.get("/briefings/{briefing_id}/pdf")
def download_pdf(briefing_id: str):
    row = service.store.get_briefing(briefing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Briefing not found")
    if row.get("paid_at") is None:
        raise HTTPException(status_code=402, detail="Payment required for PDF")
    full = service._full_from_row(row, cached=True)
    pdf_bytes = generate_pdf(full)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=briefing-{briefing_id}.pdf"},
    )
