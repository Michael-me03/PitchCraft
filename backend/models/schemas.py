from pydantic import BaseModel
from typing import Any


class ChartSpec(BaseModel):
    chart_function: str  # Name from chart_engine.AVAILABLE_CHARTS
    params: dict[str, Any]


class SlideContent(BaseModel):
    layout_type: str  # "content" | "two_column" | "chart" | "section_header" | "key_number"
                      # | "multi_chart" | "icon_grid" | "timeline" | "quote"
                      # | "agenda" | "metrics_grid" | "pricing"
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


class PresentationStructure(BaseModel):
    title: str
    subtitle: str
    author: str = ""
    slides: list[SlideContent]
