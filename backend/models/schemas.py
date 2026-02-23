from pydantic import BaseModel, field_validator
from typing import Any

# All layout types recognised by the PPTX generator.
# Unknown values from the AI are coerced to "content" rather than crashing.
_VALID_LAYOUT_TYPES: frozenset[str] = frozenset({
    "title", "agenda", "section_header", "content", "chart", "multi_chart",
    "key_number", "two_column", "comparison", "icon_grid", "timeline",
    "quote", "metrics_grid", "pricing", "closing",
})

_MAX_TITLE_LEN  = 120   # characters — prevents overflow in the title zone
_MAX_BULLETS    = 8     # bullets per column — more would be unreadable anyway


class ChartSpec(BaseModel):
    chart_function: str  # Name from chart_engine.AVAILABLE_CHARTS
    params: dict[str, Any]


class SlideContent(BaseModel):
    layout_type: str  # "content" | "two_column" | "chart" | "section_header" | "key_number"
                      # | "multi_chart" | "icon_grid" | "timeline" | "quote"
                      # | "agenda" | "metrics_grid" | "pricing" | "closing"
    title: str
    bullets: list[str] = []
    right_bullets: list[str] = []
    left_heading: str = ""
    right_heading: str = ""
    charts: list[ChartSpec] = []
    speaker_notes: str = ""
    key_number: str = ""
    key_label: str = ""
    items: list[dict] = []  # Structured data for metrics_grid and pricing layouts

    @field_validator("layout_type")
    @classmethod
    def validate_layout_type(cls, v: str) -> str:
        """Coerce unknown layout types to 'content' rather than raising."""
        return v if v in _VALID_LAYOUT_TYPES else "content"

    @field_validator("title")
    @classmethod
    def truncate_title(cls, v: str) -> str:
        """Truncate titles that would overflow the title zone."""
        return v[:_MAX_TITLE_LEN]

    @field_validator("bullets", "right_bullets", mode="before")
    @classmethod
    def cap_bullets(cls, v: list) -> list:
        """Cap bullet lists so slides remain readable."""
        return v[:_MAX_BULLETS]


class PresentationStructure(BaseModel):
    title: str
    subtitle: str
    author: str = ""
    slides: list[SlideContent]
