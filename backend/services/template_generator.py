"""
PitchCraft Template Generator
==============================
Maintains the built-in template catalog and generates blank PPTX files
with the selected template's background color applied to the slide master
and all layouts.

Each template entry defines:
  - Unique ID, display name, category, description, tags
  - Four-color palette: bg, accent, text, muted
  - Popularity / newness flags for frontend sorting
"""

# ============================================================================
# SECTION: Imports
# ============================================================================

import os
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor

# ── Path to the templates directory (relative to this file) ───────────────────
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


# ============================================================================
# SECTION: Template Catalog
# ============================================================================

TEMPLATE_CATALOG: dict[str, dict] = {

    # ── Nagarro ───────────────────────────────────────────────────────────────
    "nagarro": {
        "id": "nagarro",
        "name": "Nagarro",
        "category": "Business",
        "description": "Official Nagarro corporate template — white background with teal accent",
        "tags": ["light", "teal", "nagarro", "corporate", "official"],
        "colors": {"bg": "#FFFFFF", "accent": "#00DBA9", "text": "#0F172A", "muted": "#64748B"},
        "file": "Nagarro SE_Q3 2025_EN_presentation.pptx",
        "popular": True,
        "new": False,
    },

    # ── Business ──────────────────────────────────────────────────────────────
    "executive-dark": {
        "id": "executive-dark",
        "name": "Executive Dark",
        "category": "Business",
        "description": "Premium dark theme with gold accents for C-suite presentations",
        "tags": ["dark", "gold", "executive", "business", "premium"],
        "colors": {"bg": "#0D0D1A", "accent": "#D4AF37", "text": "#FFFFFF", "muted": "#6B6B7A"},
        "popular": True,
        "new": False,
    },
    "corporate-blue": {
        "id": "corporate-blue",
        "name": "Corporate Blue",
        "category": "Business",
        "description": "Clean light theme with blue accents, trusted by Fortune 500 companies",
        "tags": ["light", "blue", "corporate", "professional", "clean"],
        "colors": {"bg": "#F0F4FF", "accent": "#1E40AF", "text": "#1E293B", "muted": "#64748B"},
        "popular": True,
        "new": False,
    },
    "startup-pitch": {
        "id": "startup-pitch",
        "name": "Startup Pitch",
        "category": "Business",
        "description": "Bold dark theme with red energy, designed for investor pitches",
        "tags": ["dark", "red", "startup", "pitch", "bold"],
        "colors": {"bg": "#0A0A0F", "accent": "#EF4444", "text": "#FFFFFF", "muted": "#71717A"},
        "popular": False,
        "new": True,
    },
    "finance-pro": {
        "id": "finance-pro",
        "name": "Finance Pro",
        "category": "Business",
        "description": "Dark professional theme with teal highlights for financial reporting",
        "tags": ["dark", "teal", "finance", "data", "analytics"],
        "colors": {"bg": "#0C1A1A", "accent": "#14B8A6", "text": "#FFFFFF", "muted": "#6B7280"},
        "popular": False,
        "new": False,
    },

    # ── Education ─────────────────────────────────────────────────────────────
    "academic-clean": {
        "id": "academic-clean",
        "name": "Academic Clean",
        "category": "Education",
        "description": "Crisp white theme with cyan highlights for academic presentations",
        "tags": ["light", "cyan", "academic", "education", "clean"],
        "colors": {"bg": "#FFFFFF", "accent": "#0891B2", "text": "#1E293B", "muted": "#64748B"},
        "popular": True,
        "new": False,
    },
    "school-warm": {
        "id": "school-warm",
        "name": "School Warm",
        "category": "Education",
        "description": "Warm cream background with yellow accents, engaging for classrooms",
        "tags": ["warm", "yellow", "school", "classroom", "friendly"],
        "colors": {"bg": "#FFFBF0", "accent": "#D97706", "text": "#1C1917", "muted": "#78716C"},
        "popular": False,
        "new": False,
    },
    "research-purple": {
        "id": "research-purple",
        "name": "Research Purple",
        "category": "Education",
        "description": "Deep purple theme for scientific research and academic conferences",
        "tags": ["dark", "purple", "research", "scientific", "academic"],
        "colors": {"bg": "#120D1F", "accent": "#A855F7", "text": "#FFFFFF", "muted": "#9CA3AF"},
        "popular": False,
        "new": True,
    },

    # ── Creative ──────────────────────────────────────────────────────────────
    "creative-studio": {
        "id": "creative-studio",
        "name": "Creative Studio",
        "category": "Creative",
        "description": "Vibrant purple-to-pink gradient feel for creative agencies",
        "tags": ["purple", "pink", "creative", "agency", "vibrant"],
        "colors": {"bg": "#1A0A2E", "accent": "#EC4899", "text": "#FFFFFF", "muted": "#A78BFA"},
        "popular": True,
        "new": False,
    },
    "portfolio-black": {
        "id": "portfolio-black",
        "name": "Portfolio Black",
        "category": "Creative",
        "description": "Pure black with orange contrast for bold portfolio presentations",
        "tags": ["black", "orange", "portfolio", "bold", "contrast"],
        "colors": {"bg": "#000000", "accent": "#F97316", "text": "#FFFFFF", "muted": "#71717A"},
        "popular": False,
        "new": False,
    },
    "ocean-deep": {
        "id": "ocean-deep",
        "name": "Ocean Deep",
        "category": "Creative",
        "description": "Deep ocean blues for immersive storytelling presentations",
        "tags": ["blue", "ocean", "creative", "storytelling", "immersive"],
        "colors": {"bg": "#020A18", "accent": "#38BDF8", "text": "#FFFFFF", "muted": "#64748B"},
        "popular": False,
        "new": True,
    },

    # ── Minimal ───────────────────────────────────────────────────────────────
    "minimal-white": {
        "id": "minimal-white",
        "name": "Minimal White",
        "category": "Minimal",
        "description": "Timeless white theme with subtle black accents, less is more",
        "tags": ["white", "minimal", "clean", "simple", "elegant"],
        "colors": {"bg": "#FFFFFF", "accent": "#111827", "text": "#111827", "muted": "#6B7280"},
        "popular": True,
        "new": False,
    },
    "soft-pastel": {
        "id": "soft-pastel",
        "name": "Soft Pastel",
        "category": "Minimal",
        "description": "Gentle pink tones for soft, approachable presentations",
        "tags": ["pink", "pastel", "soft", "gentle", "minimal"],
        "colors": {"bg": "#FFF0F6", "accent": "#DB2777", "text": "#1E293B", "muted": "#9CA3AF"},
        "popular": False,
        "new": False,
    },

    # ── Tech ──────────────────────────────────────────────────────────────────
    "dark-tech": {
        "id": "dark-tech",
        "name": "Dark Tech",
        "category": "Tech",
        "description": "Hacker aesthetic with pure black and neon green for tech talks",
        "tags": ["black", "green", "tech", "hacker", "terminal"],
        "colors": {"bg": "#030712", "accent": "#22C55E", "text": "#FFFFFF", "muted": "#6B7280"},
        "popular": True,
        "new": False,
    },
    "cyber-blue": {
        "id": "cyber-blue",
        "name": "Cyber Blue",
        "category": "Tech",
        "description": "Futuristic dark theme with cyan for AI and tech innovation decks",
        "tags": ["dark", "cyan", "cyber", "futuristic", "AI"],
        "colors": {"bg": "#03071A", "accent": "#06B6D4", "text": "#FFFFFF", "muted": "#475569"},
        "popular": False,
        "new": True,
    },
    "forest-green": {
        "id": "forest-green",
        "name": "Forest Green",
        "category": "Tech",
        "description": "Nature-inspired green theme for sustainability and ESG presentations",
        "tags": ["green", "nature", "sustainability", "ESG", "environment"],
        "colors": {"bg": "#071A0A", "accent": "#4ADE80", "text": "#FFFFFF", "muted": "#6B7280"},
        "popular": False,
        "new": False,
    },
}


# ============================================================================
# SECTION: Color Utilities
# ============================================================================

def _hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert a CSS hex color string to an RGBColor instance."""
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _apply_background(element, rgb: RGBColor) -> None:
    """Apply a solid background color to a slide master, layout, or slide."""
    fill = element.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb


# ============================================================================
# SECTION: Template Generation
# ============================================================================

def generate_template_pptx(template_id: str) -> bytes:
    """
    Return PPTX bytes for the selected template.

    If the catalog entry has a ``file`` key pointing to an existing file in
    the templates directory, that file is returned directly so its master,
    layouts, and theme are preserved.  Otherwise a blank PPTX is generated
    with the template's background color applied to the slide master and all
    layouts.

    Args:
        template_id: Key from TEMPLATE_CATALOG.

    Returns:
        Raw bytes of the .pptx file to use as base template.

    Raises:
        ValueError: If template_id is not found in the catalog.
    """
    meta = TEMPLATE_CATALOG.get(template_id)
    if not meta:
        raise ValueError(f"Unknown template_id: {template_id!r}")

    # ── Load from actual file if available ────────────────────────────────────
    filename = meta.get("file")
    if filename:
        file_path = _TEMPLATES_DIR / filename
        if file_path.exists():
            return file_path.read_bytes()

    # ── Fallback: generate blank PPTX with background color ──────────────────
    bg_rgb = _hex_to_rgb(meta["colors"]["bg"])
    prs    = Presentation()

    # Force 16:9 widescreen (13.33" × 7.5") — python-pptx default is 4:3
    prs.slide_width  = 12_192_000   # 13.333 inches
    prs.slide_height =  6_858_000   # 7.500  inches

    _apply_background(prs.slide_master, bg_rgb)
    for layout in prs.slide_master.slide_layouts:
        _apply_background(layout, bg_rgb)

    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()


def get_template_catalog() -> list[dict]:
    """Return the template catalog as a list of metadata dicts for the API."""
    return list(TEMPLATE_CATALOG.values())
