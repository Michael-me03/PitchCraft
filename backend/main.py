"""
PitchCraft API — FastAPI Entry Point
=====================================
REST API that orchestrates the full presentation generation pipeline:
  PDF extraction → AI slide structure → Chart rendering → PPTX assembly

Endpoints:
  GET  /api/health                          Health check
  GET  /api/templates                       Template catalog
  GET  /api/download/{id}                   Download generated PPTX (30-min expiry)
  GET  /api/preview/{id}/info               Slide count for a generated PPTX
  GET  /api/preview/{id}/slide/{index}      Single slide as PNG image
  POST /api/clarify                         Check if context is sufficient
  POST /api/generate                        Main generation endpoint
  POST /api/generate-iterate                Iterate on a previous generation with feedback
"""

# ============================================================================
# SECTION: Imports & App Initialisation
# ============================================================================

import json
import logging
import traceback
import uuid

logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from services.pdf_parser import extract_text_from_pdf
from services.ai_service import (
    generate_with_quality_loop,
    generate_clarifying_questions,
    generate_iterated_structure,
)
from services.pptx_generator import generate_pptx
from services.template_generator import generate_template_pptx, get_template_catalog, TEMPLATE_CATALOG
from services.url_scraper import scrape_urls_from_prompt
from services.preview_service import convert_pptx_to_slide_images

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
_previews: dict[str, list[bytes]] = {}   # download_id → list of PNG bytes per slide


def _clean_expired() -> None:
    """Remove download and preview entries whose 30-minute window has elapsed."""
    now     = datetime.now()
    expired = [k for k, v in _downloads.items() if v["expires"] < now]
    for k in expired:
        del _downloads[k]
        _previews.pop(k, None)


def _build_summary(structure) -> str:
    """Build a human-readable summary of the generated presentation.

    Args:
        structure: PresentationStructure with title, subtitle, and slides.

    Returns:
        Multi-line markdown summary with slide count, layout breakdown,
        and section topics.
    """
    title      = structure.title or "Untitled"
    num_slides = len(structure.slides) + 1  # +1 for title slide

    # Count layout types for a breakdown
    layout_counts: dict[str, int] = {}
    for s in structure.slides:
        lt = s.layout_type or "content"
        layout_counts[lt] = layout_counts.get(lt, 0) + 1

    # Collect content slide titles (skip section headers)
    slide_titles = [s.title for s in structure.slides if s.title and s.layout_type != "section_header"]

    # Collect section headers for key topics
    sections = [s.title for s in structure.slides if s.layout_type == "section_header" and s.title]

    # Build summary
    lines: list[str] = []
    lines.append(f"**{title}** — {num_slides} Folien erstellt.")

    # Layout breakdown (only interesting types)
    layout_labels = {
        "chart": "Charts", "multi_chart": "Multi-Charts",
        "two_column": "Vergleiche", "key_number": "Kennzahlen",
        "metrics_grid": "Metriken", "pricing": "Preismodelle",
        "icon_grid": "Feature-Grids", "timeline": "Timelines",
        "quote": "Zitate", "agenda": "Agenda",
    }
    highlights = [f"{v} {layout_labels[k]}" for k, v in layout_counts.items() if k in layout_labels]
    if highlights:
        lines.append(f"Enthält: {', '.join(highlights)}")

    if sections:
        lines.append(f"Abschnitte: {' → '.join(sections[:5])}")

    return "\n".join(lines)


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
    language:    str                  = Form("de"),
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
        language=language,
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
    language:       str                  = Form("de"),
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

    # ── Scrape URLs from prompt ─────────────────────────────────────────────────
    scraped_images: list = []
    if effective_prompt.strip():
        try:
            scraped_text, scraped_images = scrape_urls_from_prompt(effective_prompt)
            if scraped_text:
                pdf_text = pdf_text + "\n\n[WEBSITE CONTENT]\n" + scraped_text
        except Exception as exc:
            logger.warning("URL scraping failed: %s", exc)

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
            language=language,
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
        pptx_bytes = generate_pptx(
            template_bytes, structure,
            template_colors=tc,
            scraped_images=scraped_images,
        )
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
        "bytes":          pptx_bytes,
        "filename":       filename,
        "expires":        datetime.now() + timedelta(minutes=30),
        "structure_json": structure.model_dump_json(),
        "pdf_text":       pdf_text,
        "user_prompt":    effective_prompt,
        "template_id":    template_id,
    }

    return JSONResponse({
        "download_id":    download_id,
        "filename":       filename,
        "quality_report": quality_report,
        "summary":        _build_summary(structure),
    })


# ============================================================================
# SECTION: Iteration Endpoint
# ============================================================================

@app.post("/api/generate-iterate")
async def iterate_presentation(
    download_id:    str                  = Form(...),
    feedback:       str                  = Form(...),
    template_file:  Optional[UploadFile] = File(None),
    template_id:    Optional[str]        = Form(None),
    purpose:        str                  = Form("business"),
    language:       str                  = Form("de"),
) -> JSONResponse:
    """
    Iterate on a previously generated presentation based on user feedback.

    Loads the previous structure and context from the download store, augments
    the prompt with the user's feedback, and regenerates the presentation.

    Args:
        download_id:    UUID of the previous generation to iterate on.
        feedback:       Free-text feedback describing desired changes.
        template_file:  Optional new PPTX template (overrides previous).
        template_id:    Optional new template ID (overrides previous).
        purpose:        Presentation style.
        language:       Output language code.

    Returns:
        JSON: {download_id: str, filename: str, quality_report: dict}

    Raises:
        HTTPException 404: If the previous download_id is unknown or expired.
        HTTPException 500: On AI generation or PPTX rendering failures.
    """
    # ── Load previous context ─────────────────────────────────────────────────
    _clean_expired()
    prev = _downloads.get(download_id)
    if not prev:
        raise HTTPException(
            status_code=404,
            detail="Previous generation not found or expired. Please generate a new presentation.",
        )

    previous_structure_json = prev.get("structure_json", "")
    pdf_text                = prev.get("pdf_text", "")
    original_prompt         = prev.get("user_prompt", "")

    # ── Resolve template bytes ────────────────────────────────────────────────
    effective_template_id = template_id or prev.get("template_id")
    if effective_template_id:
        try:
            template_bytes = generate_template_pptx(effective_template_id)
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

    # ── AI generation with feedback ───────────────────────────────────────────
    template_style = TEMPLATE_CATALOG.get(effective_template_id) if effective_template_id else None

    try:
        structure, quality_report = generate_iterated_structure(
            previous_structure_json=previous_structure_json,
            user_feedback=feedback,
            pdf_text=pdf_text,
            purpose=purpose,
            original_prompt=original_prompt,
            template_style=template_style,
            language=language,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e}")

    # ── PPTX rendering ───────────────────────────────────────────────────────
    tc = (template_style or {}).get("colors")
    try:
        pptx_bytes = generate_pptx(template_bytes, structure, template_colors=tc)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PowerPoint generation failed: {e}")

    # ── Store and return ──────────────────────────────────────────────────────
    _clean_expired()
    new_download_id = str(uuid.uuid4())
    template_name   = (template_style or {}).get("name", "Presentation")
    date_str        = datetime.now().strftime("%Y-%m-%d")
    filename        = f"PitchCraft_{template_name}_{date_str}.pptx".replace(" ", "_")

    _downloads[new_download_id] = {
        "bytes":          pptx_bytes,
        "filename":       filename,
        "expires":        datetime.now() + timedelta(minutes=30),
        "structure_json": structure.model_dump_json(),
        "pdf_text":       pdf_text,
        "user_prompt":    original_prompt,
        "template_id":    effective_template_id,
    }

    return JSONResponse({
        "download_id":    new_download_id,
        "filename":       filename,
        "quality_report": quality_report,
        "summary":        _build_summary(structure),
    })


# ============================================================================
# SECTION: Preview Endpoints
# ============================================================================

@app.get("/api/preview/{download_id}/info")
async def preview_info(download_id: str) -> JSONResponse:
    """
    Return metadata about a generated presentation's slide preview.

    Args:
        download_id: UUID string from /api/generate or /api/generate-iterate.

    Returns:
        JSON: {total_slides: int}

    Raises:
        HTTPException 404: If the download is unknown or expired.
        HTTPException 500: If preview conversion fails.
    """
    _clean_expired()
    entry = _downloads.get(download_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Download not found or expired.")

    # Generate preview if not cached
    if download_id not in _previews:
        try:
            slide_images = convert_pptx_to_slide_images(entry["bytes"])
            _previews[download_id] = slide_images
        except Exception as e:
            logger.error("Preview conversion failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Preview conversion failed: {e}")

    return JSONResponse({"total_slides": len(_previews[download_id])})


@app.get("/api/preview/{download_id}/slide/{index}")
async def preview_slide(download_id: str, index: int) -> Response:
    """
    Return a single slide as a PNG image.

    Args:
        download_id: UUID string from /api/generate or /api/generate-iterate.
        index:       Zero-based slide index.

    Returns:
        PNG image bytes.

    Raises:
        HTTPException 404: If the download or slide index is invalid.
        HTTPException 500: If preview conversion fails.
    """
    _clean_expired()
    entry = _downloads.get(download_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Download not found or expired.")

    # Generate preview if not cached
    if download_id not in _previews:
        try:
            slide_images = convert_pptx_to_slide_images(entry["bytes"])
            _previews[download_id] = slide_images
        except Exception as e:
            logger.error("Preview conversion failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Preview conversion failed: {e}")

    slides = _previews[download_id]
    if index < 0 or index >= len(slides):
        raise HTTPException(status_code=404, detail=f"Slide index {index} out of range (0-{len(slides)-1}).")

    return Response(
        content=slides[index],
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=1800"},
    )


# ============================================================================
# SECTION: Bundled Frontend (macOS .app mode)
# ============================================================================

# When running as a packaged .app the pre-built React files live one level up
# from the backend source at  Resources/web/.  Mounting them here means users
# only need to open one URL — no separate frontend server required.
_WEB_DIR = Path(__file__).parent.parent / "web"
if _WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="static")
