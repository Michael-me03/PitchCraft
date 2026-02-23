"""
PitchCraft API — FastAPI Entry Point
=====================================
REST API that orchestrates the full presentation generation pipeline:
  PDF extraction → AI slide structure → Chart rendering → PPTX assembly

Endpoints:
  GET  /api/health           Health check
  GET  /api/templates        Template catalog
  GET  /api/download/{id}    Download generated PPTX (30-min expiry)
  POST /api/clarify          Check if context is sufficient; return questions if not
  POST /api/generate         Main generation endpoint
"""

# ============================================================================
# SECTION: Imports & App Initialisation
# ============================================================================

import json
import traceback
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from services.pdf_parser import extract_text_from_pdf
from services.ai_service import generate_with_quality_loop, generate_clarifying_questions
from services.pptx_generator import generate_pptx
from services.template_generator import generate_template_pptx, get_template_catalog, TEMPLATE_CATALOG

app = FastAPI(title="PitchCraft API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# SECTION: In-Memory File Store (download_id → PPTX bytes + metadata)
# ============================================================================

_downloads: dict[str, dict] = {}


def _clean_expired() -> None:
    """Remove download entries whose 30-minute window has elapsed."""
    now     = datetime.now()
    expired = [k for k, v in _downloads.items() if v["expires"] < now]
    for k in expired:
        del _downloads[k]


# ============================================================================
# SECTION: API Endpoints
# ============================================================================

@app.get("/api/health")
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok"}


@app.get("/api/templates")
async def list_templates() -> list:
    """Return the full template catalog for the frontend gallery."""
    return get_template_catalog()


@app.get("/api/download/{download_id}")
async def download_file(download_id: str) -> Response:
    """
    Serve a previously generated PPTX file by its download ID.

    Files expire 30 minutes after generation to prevent memory accumulation.

    Args:
        download_id: UUID string returned by /api/generate.

    Raises:
        HTTPException 404: If the ID is unknown or the file has expired.
    """
    _clean_expired()
    entry = _downloads.get(download_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Download not found or expired.")
    return Response(
        content=entry["bytes"],
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{entry["filename"]}"'},
    )


@app.post("/api/clarify")
async def clarify_presentation(
    pdf_file:    Optional[UploadFile] = File(None),
    purpose:     str                  = Form("business"),
    user_prompt: str                  = Form(""),
) -> JSONResponse:
    """
    Analyse provided context and return clarifying questions if the content is
    insufficient for a high-quality presentation.

    Args:
        pdf_file:    Optional source document (.pdf or .md).
        purpose:     Presentation style — "business", "school", or "scientific".
        user_prompt: Free-text description from the user.

    Returns:
        JSON: {needs_clarification: bool, questions: [{id, question, hint}]}
    """
    # ── Extract document text ──────────────────────────────────────────────────
    pdf_text = ""
    if pdf_file is not None:
        fname = pdf_file.filename.lower()
        try:
            if fname.endswith(".md"):
                pdf_text = (await pdf_file.read()).decode("utf-8", errors="replace")
            elif fname.endswith(".pdf"):
                pdf_bytes = await pdf_file.read()
                pdf_text  = extract_text_from_pdf(pdf_bytes)
        except Exception:
            pass  # If parsing fails, proceed without document text

    result = generate_clarifying_questions(
        pdf_text=pdf_text,
        purpose=purpose,
        user_prompt=user_prompt,
    )
    return JSONResponse(result)


@app.post("/api/generate")
async def generate_presentation(
    template_file:  Optional[UploadFile] = File(None),
    template_id:    Optional[str]        = Form(None),
    pdf_file:       Optional[UploadFile] = File(None),
    purpose:        str                  = Form("business"),
    user_prompt:    str                  = Form(""),
    custom_prompt:  str                  = Form(""),
    clarifications: str                  = Form(""),
) -> JSONResponse:
    """
    Main presentation generation endpoint.

    Workflow:
    1. Validate inputs (template + prompt/PDF required)
    2. Resolve template bytes (catalog ID or uploaded file)
    3. Extract PDF text (optional)
    4. Generate slide structure via AI
    5. Render PowerPoint via PPTX generator
    6. Store file and return download ID

    Args:
        template_file:  Optional user-uploaded PPTX template.
        template_id:    Optional ID from the built-in template catalog.
        pdf_file:       Optional PDF document to analyse.
        purpose:        Presentation style — "business", "school", or "scientific".
        user_prompt:    Custom design instructions (overrides purpose preset).
        custom_prompt:  Alternative prompt field (merged with user_prompt).
        clarifications: JSON string of {question: answer} pairs from clarification step.

    Returns:
        JSON: {download_id: str, filename: str}

    Raises:
        HTTPException 400: On invalid input or missing required fields.
        HTTPException 500: On AI generation or PPTX rendering failures.
    """
    # ── Input validation ───────────────────────────────────────────────────────
    effective_prompt = user_prompt or custom_prompt
    if not effective_prompt and pdf_file is None:
        raise HTTPException(
            status_code=400,
            detail="Please provide a prompt or upload a PDF document.",
        )

    # ── Resolve template bytes ─────────────────────────────────────────────────
    if template_id:
        try:
            template_bytes = generate_template_pptx(template_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif template_file is not None:
        if not template_file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="Please upload a valid PPTX template.")
        template_bytes = await template_file.read()
    else:
        raise HTTPException(
            status_code=400,
            detail="Please select a template or upload a PPTX template file.",
        )

    # ── Extract document text (PDF or Markdown) ────────────────────────────────
    pdf_text = ""
    if pdf_file is not None:
        fname = pdf_file.filename.lower()
        if fname.endswith(".md"):
            # Markdown: read raw bytes and decode as UTF-8 — no parser needed
            try:
                pdf_text = (await pdf_file.read()).decode("utf-8", errors="replace")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read Markdown file: {e}")
            if not pdf_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="The Markdown file appears to be empty.",
                )
        elif fname.endswith(".pdf"):
            pdf_bytes = await pdf_file.read()
            try:
                pdf_text = extract_text_from_pdf(pdf_bytes)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
            if not pdf_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from PDF. The file might be image-based.",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Please upload a PDF (.pdf) or Markdown (.md) file.",
            )

    # ── AI generation ──────────────────────────────────────────────────────────
    template_style = TEMPLATE_CATALOG.get(template_id) if template_id else None

    # Parse clarifications JSON (sent from frontend as {question: answer} dict)
    parsed_clarifications: Optional[dict] = None
    if clarifications.strip():
        try:
            parsed_clarifications = json.loads(clarifications)
        except (json.JSONDecodeError, ValueError):
            pass

    try:
        structure, quality_report = generate_with_quality_loop(
            pdf_text=pdf_text,
            purpose=purpose,
            user_prompt=effective_prompt,
            template_style=template_style,
            clarifications=parsed_clarifications,
        )
        print(
            f"\n{'='*60}\n"
            f"QUALITY LOOP REPORT\n"
            f"  Attempts:      {quality_report['attempts']}\n"
            f"  Final verdict: {quality_report['final_verdict'].upper()}\n"
            + "".join(
                f"  [{h['attempt']}] {h['verdict'].upper()}"
                + (f" — {len(h['issues'])} issue(s)\n" if h['issues'] else "\n")
                + (f"      Reasoning: {h['reasoning'][:300]}...\n" if h['reasoning'] else "")
                + "".join(f"      • {iss}\n" for iss in h['issues'])
                for h in quality_report['history']
            )
            + f"{'='*60}\n"
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    # ── PPTX rendering ─────────────────────────────────────────────────────────
    tc = (template_style or {}).get("colors")   # {bg, accent, text, muted} or None
    try:
        pptx_bytes = generate_pptx(template_bytes, structure, template_colors=tc)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PowerPoint generation failed: {e}")

    # ── Store and return download link ─────────────────────────────────────────
    _clean_expired()
    download_id   = str(uuid.uuid4())
    template_name = (template_style or {}).get("name", "Presentation")
    date_str      = datetime.now().strftime("%Y-%m-%d")
    filename      = f"PitchCraft_{template_name}_{date_str}.pptx".replace(" ", "_")

    _downloads[download_id] = {
        "bytes":   pptx_bytes,
        "filename": filename,
        "expires": datetime.now() + timedelta(minutes=30),
    }

    return JSONResponse({"download_id": download_id, "filename": filename})


# ============================================================================
# SECTION: Bundled Frontend (macOS .app mode)
# ============================================================================

# When running as a packaged .app the pre-built React files live one level up
# from the backend source at  Resources/web/.  Mounting them here means users
# only need to open one URL — no separate frontend server required.
_WEB_DIR = Path(__file__).parent.parent / "web"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="static")
