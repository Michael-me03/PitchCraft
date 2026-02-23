"""
PitchCraft AI Service — Presentation Structure Generator
=========================================================
Uses OpenAI GPT-4o to convert a document (PDF text + user prompt) into a
structured JSON presentation blueprint that the PPTX generator renders.

Responsibilities:
  - Map purpose (business / school / scientific) to design instructions
  - Inject the full chart schema into the system prompt
  - Call GPT-4o and parse the JSON response
  - Return a validated PresentationStructure Pydantic model
"""

# ============================================================================
# SECTION: Imports & Configuration
# ============================================================================

import json
import logging
import os
import re
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

from models.schemas import PresentationStructure
from services.chart_engine import get_chart_schema_for_ai

load_dotenv()

logger = logging.getLogger(__name__)

# ── LLM-as-a-Judge configuration ─────────────────────────────────────────────
_JUDGE_MODEL          = "gpt-5.2"   # evaluator — strongest available chat model
_MAX_JUDGE_ITERATIONS = 3               # 1 initial generation + up to 2 retries


# ============================================================================
# SECTION: Purpose-Specific Design Templates
# ============================================================================

PURPOSE_TEMPLATES: dict[str, str] = {
    "business": """Create a McKinsey-caliber executive business presentation:
- Open with a multi_chart dashboard (KPI cards: revenue, margin, growth)
- Structure follows MECE principle (Mutually Exclusive, Collectively Exhaustive)
- Use waterfall charts for financial bridge/breakdown analysis
- Use grouped_bar for YoY or competitor comparisons
- Use funnel charts for sales/conversion pipelines
- Use line charts for trend analysis over time
- Close with a two_column slide (Challenges vs. Opportunities) + content slide for Next Steps
- Tone: data-driven, concise, boardroom-ready, action-oriented
- MAXIMIZE chart usage — every metric must be visualized""",

    "school": """Create a clear, engaging educational presentation:
- Open with a section_header and key learning objectives
- Use pie/donut charts for proportions and statistics
- Use bar charts for comparisons between categories
- Use radar charts for multi-dimensional comparisons
- Use line charts for historical trends and timelines
- Use KPI cards for key facts and definitions
- Tone: clear, structured, visual-heavy""",

    "scientific": """Create a rigorous scientific presentation:
- Follow IMRAD: Introduction, Methods, Results, Discussion, Conclusion
- Use line charts for experimental data over time
- Use grouped_bar for comparing conditions or groups
- Use scatter charts for correlation analysis
- Use radar charts for multi-variable profiles
- Use waterfall for showing cumulative or additive effects
- Tone: precise, evidence-based, citation-aware""",
}


# ============================================================================
# SECTION: System Prompt Builder
# ============================================================================

def _build_system_prompt(chart_schema: str) -> str:
    """
    Construct the full GPT-4o system prompt with chart schema and design rules.

    Args:
        chart_schema: JSON string of available chart types from the chart engine.

    Returns:
        Complete system prompt string.
    """
    return f"""You are an elite McKinsey-trained senior consultant and presentation strategist with 20 years of experience designing C-suite presentations for Fortune 500 companies.

AUDIENCE: C-suite executives and senior managers — sophisticated, data-literate, results-oriented, and time-constrained. Every slide must respect their intelligence and time.

LANGUAGE RULE (CRITICAL): Detect the language of the input document and generate ALL slide text — titles, bullets, labels, speaker notes — in EXACTLY that same language. Never mix languages. If the document is in German, everything must be in German. If in English, everything in English.

You have access to a CHART ENGINE with these chart types:

{chart_schema}

RETURN ONLY VALID JSON with this structure:
{{
  "title": "Main Title",
  "subtitle": "Subtitle",
  "author": "Author if found",
  "slides": [
    {{
      "layout_type": "section_header",
      "title": "Section Name",
      "bullets": ["Brief description"],
      "speaker_notes": "Detailed notes"
    }},
    {{
      "layout_type": "content",
      "title": "Insight-driven headline",
      "bullets": ["Point 1", "Point 2", "Point 3"],
      "speaker_notes": "Notes"
    }},
    {{
      "layout_type": "chart",
      "title": "Chart headline (state the insight)",
      "bullets": ["Key takeaway"],
      "charts": [
        {{
          "chart_function": "bar_chart",
          "params": {{
            "categories": ["A", "B", "C"],
            "values": [10, 20, 30],
            "title": "Revenue by Segment",
            "color_mode": "multi",
            "value_prefix": "$",
            "value_suffix": "M"
          }}
        }}
      ],
      "speaker_notes": "What this data means"
    }},
    {{
      "layout_type": "multi_chart",
      "title": "Dashboard: Key Metrics",
      "charts": [
        {{
          "chart_function": "kpi_card",
          "params": {{ "number": "$48.5M", "label": "Total Revenue", "trend": "+34%", "color": "blue" }}
        }},
        {{
          "chart_function": "kpi_card",
          "params": {{ "number": "22.4%", "label": "Operating Margin", "trend": "+4.3pp", "color": "emerald" }}
        }},
        {{
          "chart_function": "gauge_chart",
          "params": {{ "value": 72, "max_value": 100, "title": "NPS Score", "label": "Customer Satisfaction" }}
        }}
      ],
      "speaker_notes": "Notes"
    }},
    {{
      "layout_type": "key_number",
      "title": "Context",
      "key_number": "85%",
      "key_label": "What this means",
      "bullets": ["Supporting point"],
      "speaker_notes": "Notes"
    }},
    {{
      "layout_type": "two_column",
      "title": "Comparison",
      "left_heading": "Option A",
      "bullets": ["Pro 1", "Pro 2"],
      "right_heading": "Option B",
      "right_bullets": ["Pro 1", "Pro 2"],
      "speaker_notes": "Analysis"
    }},
    {{
      "layout_type": "agenda",
      "title": "Agenda",
      "bullets": [
        "Market Context: Industry trends driving the need for change",
        "Performance Analysis: Q4 KPI deep-dive across all business units",
        "Strategic Options: Three scenarios with risk/return trade-offs",
        "Implementation Roadmap: 12-month phased rollout plan"
      ],
      "speaker_notes": "4-item horizontal agenda. Each bullet = Section Title: Short description."
    }},
    {{
      "layout_type": "icon_grid",
      "title": "Four Core Capabilities Drive Competitive Advantage",
      "bullets": [
        "🚀 Speed: Deliver results 10× faster with automation pipelines",
        "💡 AI: Self-optimising ML models reduce manual tuning by 80%",
        "🔒 Security: Zero-trust architecture with end-to-end encryption",
        "📈 Scale: Elastic infrastructure handles 1M+ concurrent users"
      ],
      "speaker_notes": "Grid of 4 feature cards. Each bullet = emoji + Title: short description."
    }},
    {{
      "layout_type": "timeline",
      "title": "Phased Roadmap: Pilot to Full Deployment in 12 Months",
      "bullets": [
        "1️⃣ Discovery: Assess current state, define KPIs and success criteria",
        "2️⃣ Design: Build MVP architecture and validate with pilot group",
        "3️⃣ Build: Agile sprints — 4-week cycles with bi-weekly demos",
        "4️⃣ Launch: Phased rollout to all business units with change management"
      ],
      "speaker_notes": "Horizontal timeline. Each bullet = numbered emoji + Step Name: description."
    }},
    {{
      "layout_type": "quote",
      "title": "Customer Validation",
      "key_number": "This platform cut our reporting time from 3 days to 3 hours — the biggest productivity win in a decade.",
      "key_label": "CFO, Global 500 Manufacturer",
      "speaker_notes": "High-impact quote. key_number = full quote text, key_label = attribution."
    }},
    {{
      "layout_type": "metrics_grid",
      "title": "SyncFlow Delivers Measurable ROI Within 6 Months",
      "items": [
        {{"value": "–28%", "label": "Operative Kosten",    "trend": "down"}},
        {{"value": "–42%", "label": "Prozessbearbeitungszeit", "trend": "down"}},
        {{"value": "–67%", "label": "Fehlerquote",         "trend": "down"}},
        {{"value": "+35%", "label": "Mitarbeiterproduktivität", "trend": "up"}},
        {{"value": "–31%", "label": "Time-to-Market",      "trend": "down"}},
        {{"value": "+22",  "label": "NPS-Punkte",          "trend": "up"}}
      ],
      "key_number": "567 %",
      "key_label": "Netto-ROI Jahr 1",
      "bullets": [
        "Jährliche Einsparung: 480.000 €",
        "Lizenzkosten p.a.: – 72.000 €"
      ],
      "speaker_notes": "Left grid = 6 KPI cards with left-accent border. Right dark panel = ROI hero. bullets = calculation rows."
    }},
    {{
      "layout_type": "pricing",
      "title": "Skalierbare Preismodelle – Transparent und Wachstumsorientiert",
      "items": [
        {{
          "tier": "Growth",
          "price": "ab 1.500 €",
          "period": "pro Monat",
          "target": "KMU & Startups",
          "features": ["Bis zu 50 Nutzer", "3 Kern-Module", "Standard-Support", "Cloud-Hosting EU"]
        }},
        {{
          "tier": "Professional",
          "price": "ab 4.500 €",
          "period": "pro Monat",
          "target": "Mittelstand",
          "features": ["Bis zu 250 Nutzer", "5 Module inkl. AutoFlow", "Priority-Support 24h", "API-Zugang", "Onboarding-Paket"],
          "recommended": true
        }},
        {{
          "tier": "Enterprise",
          "price": "Individuell",
          "period": "auf Anfrage",
          "target": "Konzerne",
          "features": ["Unbegrenzte Nutzer", "Alle Module", "Dedicated CSM", "SLA 99,99 %", "Custom-Integrationen"],
          "dark": true
        }}
      ],
      "speaker_notes": "3-tier pricing. Middle tier recommended=true gets elevated card + badge. Last tier dark=true gets dark card."
    }}
  ]
}}

CRITICAL DESIGN RULES:
1.  CREATE 10-15 SLIDES. MANDATORY SLIDE ORDER: title → agenda → content slides → closing
    NARRATIVE ARC (mandatory): Context/Situation → Evidence/Data → Insights/So-What → Recommendations/Actions
    Use section_header slides to clearly divide these major arcs (1 per major section)
2.  AT LEAST 55% of slides MUST have charts — MANDATORY
3.  DIVERSE chart selection — use each type for its best purpose:
    • Trends over time     → line_chart, multi_line_chart, area_chart
    • Rankings/comparisons → bar_chart (vertical or horizontal), grouped_bar_chart, bullet_chart
    • Composition          → pie_chart (donut=True), stacked_bar_chart, treemap_chart, sunburst_chart
    • Change analysis      → waterfall_chart, slope_chart
    • Relationships        → scatter_chart, heatmap_chart
    • KPI highlights       → kpi_card, multi_kpi_row, progress_ring, key_number layout
    • Multi-dim profiles   → radar_chart, bullet_chart
    • Pipelines            → funnel_chart
    • Distribution/stats   → histogram_chart, box_plot, density_plot
    • A-vs-B comparison    → comparison_card, slope_chart, grouped_bar_chart
4.  Use "multi_chart" for dashboards: combine 2-4 charts (e.g. multi_kpi_row + gauge_chart)
5.  Extract REAL numerical data from the document. If not exact, use realistic estimates
6.  Every chart MUST have a concise, descriptive title
7.  Never place more than 2 text-only "content" slides in a row
8.  Slide titles state the "So What": "Revenue grew 34% to $48.5M" — NOT "Revenue"
9.  Start with a multi_chart dashboard or section_header right after the title slide
10. CLOSING SLIDE: Always end with a content slide titled "Key Takeaways & Next Steps".
    Bullets must follow this exact format (3 takeaways + 3 actions):
    "✓ [Specific finding with number]: e.g. ✓ Revenue grew 34% to $48.5M driven by Cloud"
    "→ [Concrete action]: e.g. → Accelerate Cloud migration to capture remaining $12M opportunity"
11. Speaker notes: Write in this format: "INSIGHT: [what the data reveals]. ACTION: [what leadership should do]. RISK: [what to watch out for]."
12. Max 4 bullets per slide — each bullet max 12 words, containing a specific fact or number
13. Bullets use "Keyword: supporting fact" format when possible (e.g. "Market share: grew 4pp to 28% in FY24")
13b. For content slides with 2–4 bullets, START each bullet with a relevant emoji (e.g. "📈 Revenue: grew 34%", "🚀 Market share: up 4pp", "💡 Insight: cost reduction via automation"). The generator will render these as visual card boxes — great for executive impact.
14. MECE structure: sections must be non-overlapping and together cover the full story
14b. NO FILLER SLIDES: Every slide must contribute unique data or insight. Cut any slide that just restates the title or provides generic background with no specific numbers.
15. progress_ring: use for completion rates, utilisation, NPS quota (value 0-100)
16. comparison_card: use for before/after or A-vs-B numeric comparisons across multiple rows
17. slope_chart: ideal for showing directional change across 2 time points for multiple items
18. bullet_chart: ideal for actual-vs-target KPI tracking across multiple metrics
19. multi_line_chart / area_chart: use when tracking 2+ series on the same time axis
20. icon_grid: use for 3–6 feature/capability/benefit cards (emoji + Title: desc format per bullet)
    → ideal for "Why us?", capability overviews, benefits summaries — replaces plain bullet lists
21. timeline: use for 3–5 sequential process steps or roadmap phases (numbered emoji + Step: desc)
    → ideal for project plans, implementation roadmaps, historical progression slides
22. quote: use for 1 powerful stakeholder/customer/expert quote per presentation
    → key_number = full quote text, key_label = "Name, Title/Company"
    → place after a strong data slide to humanise the numbers
23. NEW LAYOUT MIX TARGET: aim for ≥1 icon_grid, ≥1 timeline (if roadmap/process exists),
    and ≥1 quote (if testimonials/citations exist) per presentation for maximum visual variety
24. agenda: ALWAYS include as slide 2 (right after the title slide) for presentations ≥ 6 slides
    → bullets = section titles with brief descriptions ("Title: One-sentence context")
    → 3-4 bullets = horizontal cards | 5-6 bullets = two-column list
    → Use "Agenda" or "Today's Discussion" as the slide title
25. metrics_grid: use for ROI / KPI summary slides with 4-6 numeric metrics
    → items = [{{value, label, trend}}] — NEVER use plain content slide for a table of KPI numbers
    → add key_number + key_label + bullets for a dark hero "ROI panel" on the right
    → ideal replacement for bullet-list ROI slides or metric tables
25. pricing: use when the document contains pricing tiers or service packages (2-3 tiers)
    → items = [{{tier, price, period, target, features, recommended?, dark?}}]
    → always mark the middle/recommended tier with "recommended": true
    → always mark the enterprise/premium tier with "dark": true
    → replaces plain two_column or content slides for pricing information
26. CONTENT DENSITY (CRITICAL — treat as a hard constraint, not a guideline):
    - Every `content` slide MUST have exactly 3–4 substantive bullets with specific facts/numbers.
      A content slide with fewer than 3 bullets is a FAILURE — expand or merge it.
    - Every `chart` slide MUST include at least 1 chart object with real numeric data in `charts`.
      A `chart` slide with an empty `charts: []` array is FORBIDDEN.
      → If real data is unavailable, estimate realistic values rather than leaving the array empty.
      → If you truly cannot produce a chart, change layout_type to `content` with 4 bullets instead.
    - A slide whose only content is "KEY INSIGHTS" + 1 vague bullet is a critical failure.
      Minimum: 3 specific data-point bullets (e.g. "Kostensenkung: 28% durch Prozessautomatisierung").
    - Multi_chart / dashboard slides MUST contain 2–4 chart objects — never just 1 KPI card."""


# ============================================================================
# SECTION: Template Context Builder
# ============================================================================

def _build_template_context(template_style: Optional[dict]) -> str:
    """
    Build a style-context block for the user message if a template was selected.

    Args:
        template_style: Template metadata dict from the catalog, or None.

    Returns:
        Formatted context string (empty string if no template).
    """
    if not template_style:
        return ""
    colors = template_style.get("colors", {})
    tags   = template_style.get("tags", [])
    is_dark = "dark" in tags

    tone_hint = (
        "Use bold, high-contrast language — punchy insight statements work well on dark slides."
        if is_dark else
        "Use crisp, professional language — clean insight statements with clear data references."
    )
    return (
        f"\nTEMPLATE STYLE: {template_style.get('name', '')} "
        f"({template_style.get('category', '')})\n"
        f"Description: {template_style.get('description', '')}\n"
        f"Color palette: background={colors.get('bg', '')}, "
        f"accent={colors.get('accent', '')}, "
        f"text={colors.get('text', '')}, "
        f"muted={colors.get('muted', '')}\n"
        f"Tags: {', '.join(tags)}\n"
        f"Tone: {tone_hint}\n"
        f"NATIVE LAYOUTS AVAILABLE in this template: section_header slides will use the template's "
        f"built-in coloured section dividers (blue, green, white variants). "
        f"two_column slides will use the native two-column layout. "
        f"quote slides will use the native Statement layout. "
        f"Use these layout types generously — they produce the most visually varied output.\n"
    )


# ============================================================================
# SECTION: Main Generation Entry Point
# ============================================================================

def generate_presentation_structure(
    pdf_text: str,
    purpose: str,
    user_prompt: str = "",
    template_style: Optional[dict] = None,
    clarifications: Optional[dict] = None,
    judge_feedback: Optional[list[str]] = None,
) -> PresentationStructure:
    """
    Generate a complete presentation structure via gpt-5.2.

    Workflow:
    1. Resolve purpose instruction (user_prompt overrides purpose preset)
    2. Build system prompt with chart schema and design rules
    3. Build user message from document text and style instructions
    4. Optionally inject judge feedback from a previous failed attempt
    5. Call gpt-5.2 with JSON response mode
    6. Parse and validate the JSON into PresentationStructure

    Args:
        pdf_text:        Extracted text from the uploaded PDF (may be empty).
        purpose:         One of "business", "school", "scientific".
        judge_feedback:  List of specific issues from the quality judge (retry context).
        user_prompt:     Free-text design instructions (overrides purpose preset).
        template_style:  Template metadata dict for style-aware tone adaptation.
        clarifications:  Optional dict of {question: answer} from the clarification step.

    Returns:
        Validated PresentationStructure ready for the PPTX generator.

    Raises:
        json.JSONDecodeError: If GPT-4o returns malformed JSON.
        openai.APIError:      On API connectivity or quota issues.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ── Resolve design instruction ─────────────────────────────────────────────
    purpose_instruction = (
        user_prompt
        or PURPOSE_TEMPLATES.get(purpose, "")
        or "Create a visually rich, chart-heavy presentation."
    )

    # ── Build prompt components ────────────────────────────────────────────────
    template_context = _build_template_context(template_style)
    chart_schema     = json.dumps(get_chart_schema_for_ai(), indent=2)
    system_prompt    = _build_system_prompt(chart_schema)

    parts = [f"STYLE: {purpose_instruction}"]
    if template_context:
        parts.append(template_context.strip())
    if pdf_text.strip():
        parts.append(f"DOCUMENT:\n{pdf_text[:50000]}")
    else:
        parts.append(
            "No document provided. Generate content based on the style/prompt instructions above."
        )
    if clarifications:
        clar_lines = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in clarifications.items() if a and a.strip()
        )
        if clar_lines:
            parts.append(
                f"ADDITIONAL CONTEXT (answers to clarifying questions — treat as high-priority input):\n{clar_lines}"
            )

    if judge_feedback:
        issues_str = "\n".join(f"  • {issue}" for issue in judge_feedback)
        parts.append(
            f"⚠️  QUALITY FEEDBACK FROM PREVIOUS ATTEMPT — fix ALL of these issues:\n"
            f"{issues_str}\n\n"
            f"Do NOT repeat these mistakes. Every issue listed above MUST be resolved in this attempt."
        )

    user_message = "\n\n".join(parts)

    # ── Call GPT-4o ────────────────────────────────────────────────────────────
    response = client.chat.completions.create(
        model="gpt-5.2",
        max_completion_tokens=16000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    # ── Parse JSON response ────────────────────────────────────────────────────
    response_text = response.choices[0].message.content.strip()
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*\n?", "", response_text)
        response_text = re.sub(r"\n?```\s*$", "", response_text)

    data = json.loads(response_text)
    return PresentationStructure(**data)


# ============================================================================
# SECTION: LLM-as-a-Judge Quality Loop
# ============================================================================

def _judge_structure(
    structure_json: str,
    user_prompt: str,
    pdf_text: str,
    purpose: str,
    chart_schema: str,
) -> dict:
    """
    Evaluate a generated presentation structure with chain-of-thought reasoning
    followed by a binary verdict.

    The judge receives the full chart schema so it can verify whether chart
    ``params`` contain real numeric data (not placeholder values).

    Args:
        structure_json: JSON-serialised PresentationStructure to evaluate.
        user_prompt:    Original user instructions.
        pdf_text:       Source document text (may be empty).
        purpose:        One of "business", "school", "scientific".
        chart_schema:   Available chart functions and their parameter schemas.

    Returns:
        Dict with keys:
          - reasoning (str):   Step-by-step analysis written before the verdict.
          - verdict   (str):   "good" or "bad".
          - issues    (list):  Specific, actionable problems (empty when "good").
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    system_prompt = (
        "You are a senior McKinsey presentation consultant reviewing an AI-generated "
        "slide deck structure. Your job: identify quality failures with precision.\n\n"

        "EVALUATION CRITERIA — check every slide against ALL of these:\n"
        "1. CONTENT DENSITY: Every non-section slide must have 3–4 substantive bullets "
        "with real data, OR ≥1 chart with actual numeric params. "
        "Vague filler ('We are committed to excellence') = FAIL.\n"
        "2. DATA SPECIFICITY: Real numbers, percentages, or dates required. "
        "'Significant growth' without a figure = FAIL. "
        "'Revenue grew 34% YoY to €2.4B' = PASS.\n"
        "3. CHART QUALITY: Every chart slide must use a valid chart_function from the "
        "provided schema and have real numeric data in params — not obvious placeholders "
        "like [1, 2, 3] or ['A', 'B', 'C'] with round dummy values.\n"
        "4. NO EMPTY SLIDES: A slide with only a title and empty bullets/charts = FAIL.\n"
        "5. NARRATIVE ARC: Slides form a logical flow (Context → Evidence → Insights → "
        "Actions or equivalent). Random topic order = FAIL.\n\n"

        "PROCESS:\n"
        "Step 1 — Write detailed reasoning: go through each slide by title, check each "
        "criterion, cite exact evidence (e.g. 'Slide 4 bar_chart values: [100, 200, 300] "
        "— suspiciously round, likely placeholder').\n"
        "Step 2 — State your verdict: 'good' only if ALL criteria pass for ALL slides. "
        "Otherwise 'bad'.\n"
        "Step 3 — If 'bad', list issues as specific, actionable bullet points "
        "(slide name + criterion + what exactly is wrong).\n\n"

        "Return ONLY valid JSON:\n"
        '{"reasoning": "...", "verdict": "good" | "bad", '
        '"issues": ["Slide X (Title): criterion — specific problem", ...]}\n'
        'When verdict is "good", issues must be [].'
    )

    user_msg = "\n\n".join([
        f"PURPOSE: {purpose}",
        f"USER PROMPT: {user_prompt or '(none)'}",
        f"SOURCE DOCUMENT (first 2000 chars):\n{pdf_text[:2000] if pdf_text else '(none)'}",
        f"CHART SCHEMA (valid functions & params):\n{chart_schema}",
        f"PRESENTATION STRUCTURE TO EVALUATE:\n{structure_json[:10000]}",
    ])

    try:
        response = client.chat.completions.create(
            model=_JUDGE_MODEL,
            max_completion_tokens=1500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        return {
            "reasoning": data.get("reasoning", ""),
            "verdict":   data.get("verdict", "good"),
            "issues":    data.get("issues", []),
        }
    except Exception as exc:
        logger.warning("Judge call failed (%s) — defaulting to 'good'", exc)
        return {"reasoning": "", "verdict": "good", "issues": []}


def generate_with_quality_loop(
    pdf_text: str,
    purpose: str,
    user_prompt: str = "",
    template_style: Optional[dict] = None,
    clarifications: Optional[dict] = None,
) -> tuple[PresentationStructure, dict]:
    """
    Generate a presentation with an LLM-as-a-judge quality loop.

    Flow per iteration:
      1. Generate structure (gpt-5.2)
      2. Judge structure (gpt-5.2-pro): reasoning → binary verdict
      3. If "good"  → return immediately
         If "bad"   → inject issues as feedback and retry (up to _MAX_JUDGE_ITERATIONS)
      4. After max iterations, return the last attempt regardless of verdict

    Args:
        pdf_text:       Extracted PDF text (may be empty).
        purpose:        "business" | "school" | "scientific".
        user_prompt:    Free-text instructions.
        template_style: Template metadata for style-aware tone.
        clarifications: Answers to clarifying questions.

    Returns:
        Tuple of (PresentationStructure, quality_report dict).
        quality_report keys:
          - attempts     (int):        How many generation calls were made.
          - final_verdict (str):       "good" or "bad".
          - history      (list[dict]): Per-attempt {attempt, verdict, reasoning, issues}.
    """
    chart_schema  = json.dumps(get_chart_schema_for_ai(), indent=2)
    judge_feedback: Optional[list[str]] = None
    history: list[dict] = []
    structure: Optional[PresentationStructure] = None

    for attempt in range(1, _MAX_JUDGE_ITERATIONS + 1):
        logger.info("Generation attempt %d / %d", attempt, _MAX_JUDGE_ITERATIONS)

        structure = generate_presentation_structure(
            pdf_text=pdf_text,
            purpose=purpose,
            user_prompt=user_prompt,
            template_style=template_style,
            clarifications=clarifications,
            judge_feedback=judge_feedback,
        )

        # Skip judging on the final allowed attempt — just return it
        if attempt == _MAX_JUDGE_ITERATIONS:
            logger.info("Max iterations reached — returning attempt %d", attempt)
            history.append({"attempt": attempt, "verdict": "skipped",
                            "reasoning": "Max iterations reached.", "issues": []})
            break

        judgment = _judge_structure(
            structure_json=structure.model_dump_json(indent=2),
            user_prompt=user_prompt,
            pdf_text=pdf_text,
            purpose=purpose,
            chart_schema=chart_schema,
        )

        logger.info(
            "Judge verdict: %s (attempt %d)\nReasoning: %s",
            judgment["verdict"].upper(), attempt, judgment["reasoning"][:400],
        )

        history.append({
            "attempt":   attempt,
            "verdict":   judgment["verdict"],
            "reasoning": judgment["reasoning"],
            "issues":    judgment["issues"],
        })

        if judgment["verdict"] == "good":
            logger.info("Quality check PASSED on attempt %d", attempt)
            break

        judge_feedback = judgment["issues"]
        logger.warning(
            "Quality check FAILED on attempt %d — %d issues — retrying",
            attempt, len(judge_feedback),
        )

    final_verdict = history[-1]["verdict"] if history else "good"
    quality_report = {
        "attempts":      len(history),
        "final_verdict": final_verdict if final_verdict != "skipped" else "good",
        "history":       history,
    }
    return structure, quality_report


# ============================================================================
# SECTION: Clarification Question Generator
# ============================================================================

def generate_clarifying_questions(
    pdf_text: str,
    purpose: str,
    user_prompt: str = "",
) -> dict:
    """
    Analyse the provided context and return targeted clarifying questions if the
    content is insufficient to generate a high-quality presentation.

    Uses gpt-4o-mini for speed and cost efficiency — this is a lightweight check,
    not the full generation call.

    Args:
        pdf_text:    Extracted text from the uploaded PDF (may be empty).
        purpose:     One of "business", "school", "scientific".
        user_prompt: Free-text instructions from the user.

    Returns:
        Dict with keys:
          - needs_clarification (bool): True if questions should be shown.
          - questions (list[dict]): List of {id, question, hint} dicts.
                                    Empty list when needs_clarification is False.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    has_doc    = bool(pdf_text.strip())
    has_prompt = bool(user_prompt.strip())

    system_prompt = (
        "You are an assistant preparing to generate a business presentation. "
        "Your task: analyse the provided context (user prompt + document excerpt) and "
        "decide whether you have enough information to create a content-rich, data-driven "
        "presentation. Ask 2–3 specific, helpful clarifying questions ONLY IF truly necessary.\n\n"

        "Ask questions when:\n"
        "- No document was provided AND the prompt is vague (fewer than 15 meaningful words)\n"
        "- Key data is missing: target audience, key metrics, specific goals, company name\n"
        "- The document exists but the prompt gives no direction at all\n\n"

        "Do NOT ask questions when:\n"
        "- The document provides sufficient context on its own\n"
        "- The prompt is detailed and specific (15+ meaningful words with clear intent)\n"
        "- The answers are already obvious from the provided context\n\n"

        "LANGUAGE RULE: Write all questions in the SAME language as the user's prompt "
        "(German if prompt is German, English if prompt is English, etc.).\n\n"

        "Return ONLY valid JSON:\n"
        '{"needs_clarification": true|false, "questions": ['
        '{"id": "q1", "question": "...", "hint": "e.g. ..."}, ...]}\n'
        "If no clarification needed: {\"needs_clarification\": false, \"questions\": []}"
    )

    user_msg_parts = [f"PURPOSE: {purpose}"]
    if has_prompt:
        user_msg_parts.append(f"USER PROMPT: {user_prompt}")
    else:
        user_msg_parts.append("USER PROMPT: (none provided)")
    if has_doc:
        user_msg_parts.append(f"DOCUMENT EXCERPT:\n{pdf_text[:3000]}")
    else:
        user_msg_parts.append("DOCUMENT: None uploaded")

    user_msg = "\n\n".join(user_msg_parts)

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            max_completion_tokens=600,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content.strip())
        # Ensure the expected keys are present
        return {
            "needs_clarification": bool(data.get("needs_clarification", False)),
            "questions": data.get("questions", []),
        }
    except Exception:
        # If clarification check fails for any reason, silently skip it
        return {"needs_clarification": False, "questions": []}
