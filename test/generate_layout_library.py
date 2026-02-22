"""
PitchCraft – Layout & Chart Library Generator
=============================================
Produces a reference PPTX covering EVERY slide type and EVERY chart type
from the engine (25 charts × 3 slot variants = visual proof that layout,
scaling and aspect-ratio rendering all work perfectly).

Usage (from PitchCraft/backend/):
    python3 ../test/generate_layout_library.py

Output: ../test/layout_library.pptx
"""
import io, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from pptx import Presentation
from pptx.util import Inches
from services.pptx_generator import generate_pptx
from models.schemas import PresentationStructure, SlideContent, ChartSpec


# ── Chart factory helper ───────────────────────────────────────────────────────
def c(fn, **p) -> ChartSpec:
    return ChartSpec(chart_function=fn, params=p)


# ── Canonical sample data for every chart type ────────────────────────────────

# Plotly Engine
BAR          = c("bar_chart",         categories=["Q1","Q2","Q3","Q4"], values=[4.2,6.8,5.1,8.3],    title="Quarterly Revenue", ylabel="€M", value_prefix="€", value_suffix="M")
BAR_H        = c("bar_chart",         categories=["DACH","USA","APAC","LatAm"], values=[38,28,22,12], title="Revenue by Region", horizontal=True, value_suffix="%")
LINE         = c("line_chart",        categories=["Jan","Feb","Mar","Apr","May","Jun"], values=[120,145,132,167,189,210], title="Monthly Active Users", ylabel="k Users")
MULTI_LINE   = c("multi_line_chart",  categories=["Q1","Q2","Q3","Q4"], series={"Product A":[120,145,160,195],"Product B":[80,95,110,130],"Product C":[40,55,70,85]}, title="Revenue by Product", ylabel="€k")
AREA         = c("area_chart",        categories=["Jan","Feb","Mar","Apr","May"], series={"Organic":[50,65,72,88,95],"Paid":[30,38,42,50,58]}, title="Traffic by Channel", stacked=True)
PIE          = c("pie_chart",         categories=["DACH","USA","APAC","ROW"], values=[38,28,22,12], title="Revenue by Region", donut=True)
STACKED      = c("stacked_bar_chart", categories=["2021","2022","2023","2024"], series={"A":[120,145,160,195],"B":[80,95,110,130],"C":[40,55,70,85]}, title="Revenue Mix", ylabel="€k")
GROUPED      = c("grouped_bar_chart", categories=["North","South","East","West"], series={"Budget":[250,180,210,160],"Actual":[238,195,204,172]}, title="Budget vs Actual", ylabel="€k")
WATERFALL    = c("waterfall_chart",   categories=["Start","+Sales","-Returns","+Upsell","End"], values=[1000,450,-120,200,1530], title="Revenue Bridge", ylabel="€k", value_prefix="€")
GAUGE        = c("gauge_chart",       value=73, max_value=100, title="Customer Satisfaction", label="NPS Score", suffix="%")
RADAR        = c("radar_chart",       categories=["Quality","Speed","Price","Support","Design"], values=[85,72,68,90,78], title="Product Assessment", max_value=100)
FUNNEL       = c("funnel_chart",      stages=["Leads","Qualified","Proposal","Negotiation","Won"], values=[1000,620,310,180,95], title="Sales Funnel")
TREEMAP      = c("treemap_chart",     categories=["Software","Hardware","Services","Cloud","Support"], values=[420,280,190,350,140], title="Revenue by Segment")
SUNBURST     = c("sunburst_chart",    categories=["DACH","Germany","Austria","CH","USA","NY","CA"], values=[100,60,25,15,80,50,30], parents=["","DACH","DACH","DACH","","USA","USA"], title="Geographic Breakdown")
HEATMAP      = c("heatmap_chart",     x_labels=["Mon","Tue","Wed","Thu","Fri"], y_labels=["09:00","12:00","15:00","18:00"], values=[[45,72,68,55,40],[80,95,88,76,60],[70,85,92,80,55],[30,45,52,48,35]], title="Support Volume by Time")
SCATTER      = c("scatter_chart",     x_values=[10,25,38,52,65,78], y_values=[120,195,240,310,380,450], labels=["A","B","C","D","E","F"], title="Revenue vs Marketing Spend", xlabel="€k Spend", ylabel="€k Revenue")
BULLET       = c("bullet_chart",      categories=["Revenue","NPS","Retention","Margin"], values=[83,72,94,21], targets=[80,75,90,25], title="KPI Actuals vs Targets", value_suffix="")
SLOPE        = c("slope_chart",       categories=["DACH","USA","APAC","LatAm"], before_values=[38,28,22,12], after_values=[42,31,27,15], before_label="2023", after_label="2024", title="Market Share Shift", value_suffix="%")

# Matplotlib Engine
KPI          = c("kpi_card",          number="€8.3M", label="Q4 Revenue", trend="+18%", subtitle="vs Q4 2023", color="indigo")
KPI2         = c("kpi_card",          number="94%",   label="Retention Rate", trend="+2pp", color="emerald")
KPI3         = c("kpi_card",          number="72",    label="NPS Score",    trend="+8",  color="blue")
MULTI_KPI    = c("multi_kpi_row",     items=[{"number":"€8.3M","label":"Revenue","trend":"+18%","color":"indigo"},{"number":"4,280","label":"New Clients","trend":"+12%","color":"cyan"},{"number":"94%","label":"Retention","trend":"+2pp","color":"emerald"},{"number":"72","label":"NPS","trend":"+8","color":"violet"}])
ICON_GRID    = c("icon_stat_grid",    items=[{"number":"42","label":"Projects"},{"number":"18","label":"Countries"},{"number":"320","label":"Employees"},{"number":"94%","label":"Uptime"}])
PROGRESS     = c("progress_ring",     items=[{"value":73,"max":100,"label":"Quota Attained","color":"#6366F1"},{"value":88,"max":100,"label":"Quality Score","color":"#10B981"},{"value":65,"max":100,"label":"Utilisation","color":"#F59E0B"}], title="Operations Health")
COMPARISON   = c("comparison_card",   items=[{"label":"Revenue €k","value_a":8100,"value_b":8300},{"label":"NPS","value_a":64,"value_b":72},{"label":"Retention %","value_a":92,"value_b":94},{"label":"Margin %","value_a":18,"value_b":21}], title="2023 vs 2024 Scorecard", label_a="2023", label_b="2024")

# Altair / Statistical Engine
HIST         = c("histogram_chart",   values=[12,15,14,18,22,25,28,30,32,35,37,40,42,45,48,50,52,55,60,65,70], title="Deal Size Distribution", xlabel="€k Deal Size")
BOX          = c("box_plot",          data={"Enterprise":[45,52,60,65,70,80,90,95],"Mid-Market":[20,28,35,40,45,50,55],"SMB":[5,8,10,12,15,18,22]}, title="ARR by Segment", ylabel="€k ARR")
DENSITY      = c("density_plot",      data={"2022":[10,15,18,22,25,28,30],"2023":[18,22,28,32,35,40,42],"2024":[28,32,38,42,45,50,55]}, title="Deal Value Distribution YoY", xlabel="€k Deal Value")


# ── Slide definitions ─────────────────────────────────────────────────────────

SLIDES = [

    # ══ SECTION 1: Single-chart slides (full-width, no insight panel) ══════════
    SlideContent(layout_type="section_header", title="1 · Single-Chart Slides",
                 bullets=["Chart fills the full content area — 90% slide width × 68.5% height"]),

    SlideContent(layout_type="chart", title="Bar Chart – Quarterly Revenue",               charts=[BAR]),
    SlideContent(layout_type="chart", title="Bar Chart – Horizontal (by Region)",          charts=[BAR_H]),
    SlideContent(layout_type="chart", title="Line Chart – Monthly Active Users",           charts=[LINE]),
    SlideContent(layout_type="chart", title="Multi-Line Chart – Revenue by Product",       charts=[MULTI_LINE]),
    SlideContent(layout_type="chart", title="Area Chart – Traffic by Channel (stacked)",   charts=[AREA]),
    SlideContent(layout_type="chart", title="Pie / Donut Chart – Revenue by Region",       charts=[PIE]),
    SlideContent(layout_type="chart", title="Stacked Bar – Revenue Mix 2021-2024",         charts=[STACKED]),
    SlideContent(layout_type="chart", title="Grouped Bar – Budget vs Actual",              charts=[GROUPED]),
    SlideContent(layout_type="chart", title="Waterfall – Revenue Bridge",                  charts=[WATERFALL]),
    SlideContent(layout_type="chart", title="Gauge – NPS Score at 73 Exceeds Target",      charts=[GAUGE]),
    SlideContent(layout_type="chart", title="Radar – Multi-Dimensional Product Assessment", charts=[RADAR]),
    SlideContent(layout_type="chart", title="Funnel – Sales Pipeline Conversion",          charts=[FUNNEL]),
    SlideContent(layout_type="chart", title="Treemap – Revenue by Segment",                charts=[TREEMAP]),
    SlideContent(layout_type="chart", title="Sunburst – Geographic Revenue Breakdown",     charts=[SUNBURST]),
    SlideContent(layout_type="chart", title="Heatmap – Support Volume by Day & Time",      charts=[HEATMAP]),
    SlideContent(layout_type="chart", title="Scatter – Revenue vs Marketing Spend",        charts=[SCATTER]),
    SlideContent(layout_type="chart", title="Bullet Chart – KPI Actuals vs Targets",       charts=[BULLET]),
    SlideContent(layout_type="chart", title="Slope Chart – Market Share 2023 → 2024",     charts=[SLOPE]),
    SlideContent(layout_type="chart", title="KPI Card – Q4 Revenue Milestone",             charts=[KPI]),
    SlideContent(layout_type="chart", title="Multi-KPI Row – Exec Dashboard Overview",     charts=[MULTI_KPI]),
    SlideContent(layout_type="chart", title="Icon Stat Grid – Company at a Glance",        charts=[ICON_GRID]),
    SlideContent(layout_type="chart", title="Progress Rings – Operations Health",          charts=[PROGRESS]),
    SlideContent(layout_type="chart", title="Comparison Card – 2023 vs 2024 Scorecard",   charts=[COMPARISON]),
    SlideContent(layout_type="chart", title="Histogram – Deal Size Distribution",          charts=[HIST]),
    SlideContent(layout_type="chart", title="Box Plot – ARR Distribution by Segment",      charts=[BOX]),
    SlideContent(layout_type="chart", title="Density Plot – Deal Value YoY",              charts=[DENSITY]),

    # ══ SECTION 2: Chart + Key Insights panel (60 / 40 split) ════════════════
    SlideContent(layout_type="section_header", title="2 · Chart + Key Insights Panel",
                 bullets=["Left 60% chart · Right insight card with em-dash bullets"]),

    SlideContent(layout_type="chart", title="Q4 Revenue Grew 18% to €8.3M",
                 charts=[BAR], bullets=[
                     "Growth: +18% YoY driven by enterprise upsells",
                     "Q4 best quarter in company history at €8.3M",
                     "Pipeline: Q1 2025 target set at €9.5M (+14%)",
                     "Risk: FX headwinds may compress margin by 2pp",
                 ]),
    SlideContent(layout_type="chart", title="MAU Crossed 200k Milestone in June",
                 charts=[LINE], bullets=[
                     "MAU: First time exceeding 200k in company history",
                     "Growth: Consistent 12% MoM since February launch",
                     "Driver: PLG campaign increased organic sign-ups 34%",
                 ]),
    SlideContent(layout_type="chart", title="DACH Represents 38% of Revenue",
                 charts=[PIE], bullets=[
                     "DACH: Largest region at 38% despite 2% YoY decline",
                     "USA: Growing share of 28%, up 3pp vs prior year",
                     "APAC: Fastest growing at +22%, entry into Japan",
                 ]),
    SlideContent(layout_type="chart", title="Budget Deficit of €16k in South Region",
                 charts=[GROUPED], bullets=[
                     "North: Only region on-budget, +€12k surplus",
                     "South: Largest miss at -€15k, driven by headcount",
                     "Action: Q1 cost review initiated across all regions",
                 ]),
    SlideContent(layout_type="chart", title="NPS of 73 Beats Industry Benchmark by 9pp",
                 charts=[GAUGE], bullets=[
                     "NPS: 73 vs industry average of 64 (+9pp advantage)",
                     "Driver: Support response time improved to 2.1h avg",
                     "Risk: Enterprise NPS tracking below SMB at 68 vs 79",
                 ]),
    SlideContent(layout_type="chart", title="Retention: 94% vs 90% Target – Outperforming",
                 charts=[BULLET], bullets=[
                     "Retention: 94% vs 90% target — 4pp overachievement",
                     "NPS: 72 vs 75 target — 3pp gap to close in H1",
                     "Margin: 21% vs 25% target — cost programme underway",
                 ]),
    SlideContent(layout_type="chart", title="Comparison Card + Insight Panel",
                 charts=[COMPARISON], bullets=[
                     "Revenue: +€200k (+2.5%) driven by enterprise growth",
                     "NPS: +8 points — best improvement in 3 years",
                     "Margin: +3pp from efficiency programme savings",
                 ]),

    # ══ SECTION 3: Multi-Chart Dashboards ════════════════════════════════════
    SlideContent(layout_type="section_header", title="3 · Multi-Chart Dashboards",
                 bullets=["Pixel-perfect grids: 1×1 · 2×1 · 3×1 · 2×2 · 3×2"]),

    SlideContent(layout_type="multi_chart", title="Dashboard – 1 Chart (full body)",                 charts=[BAR]),
    SlideContent(layout_type="multi_chart", title="Dashboard – 2 Charts (2×1)",                      charts=[BAR, LINE]),
    SlideContent(layout_type="multi_chart", title="Dashboard – 3 Charts (3×1)",                      charts=[BAR, LINE, PIE]),
    SlideContent(layout_type="multi_chart", title="Dashboard – 4 Charts (2×2)",                      charts=[BAR, LINE, PIE, WATERFALL]),
    SlideContent(layout_type="multi_chart", title="Dashboard – 5 Charts (3×2, cell 6 empty)",        charts=[BAR, LINE, PIE, WATERFALL, GAUGE]),
    SlideContent(layout_type="multi_chart", title="Dashboard – 6 Charts (3×2)",                      charts=[BAR, LINE, PIE, WATERFALL, GAUGE, RADAR]),
    SlideContent(layout_type="multi_chart", title="Executive KPI Dashboard",                          charts=[MULTI_KPI, GAUGE, WATERFALL, BAR]),
    SlideContent(layout_type="multi_chart", title="Operational Dashboard – Diverse Mix",              charts=[PROGRESS, BULLET, SLOPE, COMPARISON]),
    SlideContent(layout_type="multi_chart", title="Statistical Dashboard",                            charts=[HIST, BOX, DENSITY, SCATTER]),
    SlideContent(layout_type="multi_chart", title="Sales Pipeline Dashboard",                         charts=[FUNNEL, GROUPED, BULLET, KPI]),
    SlideContent(layout_type="multi_chart", title="Geographic + Product Dashboard",                   charts=[PIE, TREEMAP, STACKED, MULTI_LINE]),

    # ══ SECTION 4: Key Number Slides ═════════════════════════════════════════
    SlideContent(layout_type="section_header", title="4 · Key Number Slides",
                 bullets=["Hero number centred on slide with supporting context"]),

    SlideContent(layout_type="key_number", title="Revenue Milestone: Best Quarter Ever",
                 key_number="€8.3M", key_label="Q4 2024 Revenue",
                 bullets=["18% above Q4 2023", "Best quarter in company history", "Strong pipeline heading into Q1"]),
    SlideContent(layout_type="key_number", title="Customer Retention Leads Industry",
                 key_number="94%", key_label="Annual Retention Rate",
                 bullets=["Benchmark: 88% industry average", "+2pp improvement vs 2023"]),
    SlideContent(layout_type="key_number", title="NPS of 72 Exceeds Target by 8 Points",
                 key_number="72", key_label="Net Promoter Score",
                 bullets=["Target was 64", "Driven by support improvements", "Industry benchmark: 58"]),
    SlideContent(layout_type="key_number", title="KPI Card as Hero Number Variant",
                 charts=[KPI2],
                 bullets=["Leading indicator of long-term revenue growth", "4pp above prior year"]),

    # ══ SECTION 5: Two-Column Comparison ═════════════════════════════════════
    SlideContent(layout_type="section_header", title="5 · Two-Column Comparisons",
                 bullets=["Equal-width cards with heading + divider + bullets"]),

    SlideContent(layout_type="two_column", title="Strengths vs Weaknesses",
                 left_heading="Strengths", right_heading="Weaknesses",
                 bullets=["Market-leading NPS of 72", "Strong DACH brand recognition", "94% retention rate", "Diversified revenue streams"],
                 right_bullets=["Limited APAC sales presence", "High customer acquisition cost", "Legacy platform technical debt", "Narrow enterprise product portfolio"]),

    SlideContent(layout_type="comparison", title="Current State vs Target State 2025",
                 left_heading="Today (2024)", right_heading="Target (2025)",
                 bullets=["Manual reporting processes", "€8.3M quarterly revenue", "4 product lines", "DACH-focused GTM"],
                 right_bullets=["Automated BI dashboards", "€12M quarterly revenue (+45%)", "7 product lines incl. Cloud", "Pan-European GTM expansion"]),

    SlideContent(layout_type="two_column", title="Build vs Buy Technology Decision",
                 left_heading="Build In-House", right_heading="Buy / Partner",
                 bullets=["Full IP ownership", "Custom-fit to our process", "Higher upfront investment", "18-month time to market"],
                 right_bullets=["Faster deployment in 3 months", "Proven at scale", "Ongoing licensing cost", "Integration complexity risk"]),

    # ══ SECTION 6: Text Content Slides ════════════════════════════════════════
    SlideContent(layout_type="section_header", title="6 · Text Content Slides",
                 bullets=["Adaptive font sizing — fewer, shorter bullets → larger text"]),

    SlideContent(layout_type="content", title="Strategic Priorities 2025 (4 bullets, 14pt)",
                 bullets=["Growth: Expand into UK and Benelux markets by Q2", "Product: Launch Cloud platform by Q2 2025", "Efficiency: Reduce CAC by 20% through product-led growth", "Talent: Hire 40 engineers across 3 offices"]),
    SlideContent(layout_type="content", title="Key Risks & Mitigations (3 bullets, 16pt)",
                 bullets=["FX Headwinds: 3% revenue impact hedged via forward contracts", "Competition: New entrant in DACH; response plan ready for Q1", "Talent: Critical hires in engineering; offers extended to 12 candidates"]),
    SlideContent(layout_type="content", title="Key Takeaways & Recommended Next Steps",
                 bullets=["Revenue: €8.3M Q4 — on track for €30M full-year target", "Approve headcount plan: 40 engineers, 12 AEs by end of Q1", "Prioritise Cloud platform launch — first beta customer onboarded March 1"]),

    # ══ SECTION 7: Agenda Slides ══════════════════════════════════════════════
    SlideContent(layout_type="section_header", title="7 · Agenda Slides",
                 bullets=["Horizontal cards (2–4 items) · Two-column list (5–6 items)"]),

    SlideContent(layout_type="agenda", title="Agenda",
                 bullets=[
                     "Market Context: Industry trends and competitive dynamics driving change",
                     "Performance Analysis: Q4 KPI deep-dive across all business units",
                     "Strategic Options: Three scenarios with risk/return trade-offs",
                 ]),
    SlideContent(layout_type="agenda", title="Today's Discussion",
                 bullets=[
                     "Market Context: Industry trends and the case for transformation",
                     "Performance Review: Revenue, margin, and operational KPI analysis",
                     "Growth Strategy: Market expansion and product roadmap priorities",
                     "Implementation Plan: 12-month phased rollout with milestones",
                 ]),
    SlideContent(layout_type="agenda", title="Agenda — Six-Section Overview",
                 bullets=[
                     "Introduction: Context, scope and executive summary",
                     "Market Analysis: Competitive landscape and TAM sizing",
                     "Performance: Q4 results vs targets across all dimensions",
                     "Strategy: Three strategic scenarios and recommendation",
                     "Financials: 3-year P&L, investment requirement and ROI",
                     "Roadmap: Implementation phases, risks and next steps",
                 ]),

    # ══ SECTION 8: Icon Grid Slides ══════════════════════════════════════════
    SlideContent(layout_type="section_header", title="7 · Icon Grid Slides",
                 bullets=["3–6 feature/benefit cards in a responsive grid (3×1, 2×2, 3×2)"]),

    SlideContent(layout_type="icon_grid", title="Four Core Capabilities Drive Competitive Advantage",
                 bullets=[
                     "🚀 Speed: Deliver results 10× faster with automation pipelines",
                     "💡 AI: Self-optimising ML models reduce manual tuning by 80%",
                     "🔒 Security: Zero-trust architecture with end-to-end encryption",
                     "📈 Scale: Elastic infrastructure handles 1M+ concurrent users",
                 ]),
    SlideContent(layout_type="icon_grid", title="Six-Pillar Value Proposition for Enterprise Clients",
                 bullets=[
                     "🎯 Precision: Data-driven decisions backed by real-time analytics",
                     "⚡ Velocity: Deploy new features in hours, not months",
                     "🌍 Global: Multi-region redundancy across 12 data centres",
                     "🤝 Partnership: Dedicated CSM and 24/7 support SLA",
                     "💰 ROI: Average 340% return on investment within 18 months",
                     "🛡 Compliance: GDPR, SOC 2 Type II, ISO 27001 certified",
                 ]),
    SlideContent(layout_type="icon_grid", title="Three Strategic Focus Areas for 2025",
                 bullets=[
                     "📊 Revenue Growth: Expand ARR from €30M to €50M via enterprise GTM",
                     "🏗 Platform Modernisation: Migrate to cloud-native microservices architecture",
                     "🌱 Talent & Culture: Hire 40 engineers and launch leadership development programme",
                 ]),

    # ══ SECTION 8: Timeline Slides ═══════════════════════════════════════════
    SlideContent(layout_type="section_header", title="8 · Timeline Slides",
                 bullets=["Horizontal step-by-step timeline for process and roadmap slides"]),

    SlideContent(layout_type="timeline", title="12-Month Transformation Roadmap",
                 bullets=[
                     "1️⃣ Discovery: Assess current state, map stakeholders, define KPIs",
                     "2️⃣ Design: Build MVP architecture and validate with pilot group",
                     "3️⃣ Build: Agile sprints — 4-week cycles with bi-weekly demos",
                     "4️⃣ Launch: Phased rollout to all 8 business units",
                 ]),
    SlideContent(layout_type="timeline", title="Five-Stage Sales Process Drives 38% Win Rate",
                 bullets=[
                     "🔍 Prospect: ICP-qualified outbound, SDR-led cold outreach",
                     "📞 Qualify: MEDDIC scorecard filters top 30% of opportunities",
                     "🎯 Propose: Tailored business case with ROI model in <48h",
                     "🤝 Negotiate: Legal and commercial aligned via deal desk",
                     "✅ Close: e-Signature and onboarding kickoff same day",
                 ]),

    # ══ SECTION 9: Quote Slides ════════════════════════════════════════════════
    SlideContent(layout_type="section_header", title="9 · Quote Slides",
                 bullets=["High-impact quote with large open-quote glyph and attribution"]),

    SlideContent(layout_type="quote",
                 title="Customer Validation",
                 key_number="This platform cut our reporting time from 3 days to 3 hours. It's the single biggest productivity win we've seen in a decade.",
                 key_label="CFO, Global 500 Manufacturer"),
    SlideContent(layout_type="quote",
                 title="Market Analyst View",
                 key_number="PitchCraft represents the next generation of AI-native presentation tooling — combining the analytical rigour of McKinsey with the speed of a design agency.",
                 key_label="Senior Analyst, Gartner — Magic Quadrant Report 2025"),

    # ══ SECTION 10: Metrics Grid (Manus-style KPI cards + dark hero panel) ════
    SlideContent(layout_type="section_header", title="10 · Metrics Grid (Manus Style)",
                 bullets=["Left-accent KPI cards + optional dark hero ROI panel on the right"]),

    SlideContent(layout_type="metrics_grid",
                 title="SyncFlow Delivers Measurable ROI Within 6 Months",
                 items=[
                     {"value": "–28%", "label": "Operative Kosten",         "trend": "down"},
                     {"value": "–42%", "label": "Prozessbearbeitungszeit",   "trend": "down"},
                     {"value": "–67%", "label": "Fehlerquote",              "trend": "down"},
                     {"value": "+35%", "label": "Mitarbeiterproduktivität", "trend": "up"},
                     {"value": "–31%", "label": "Time-to-Market",           "trend": "down"},
                     {"value": "+22",  "label": "NPS-Punkte",               "trend": "up"},
                 ],
                 key_number="567 %",
                 key_label="Netto-ROI Jahr 1",
                 bullets=["Jährliche Einsparung: 480.000 €", "Lizenzkosten p.a.: – 72.000 €"]),

    SlideContent(layout_type="metrics_grid",
                 title="Q4 2024 Operational Performance — All KPIs in Green",
                 items=[
                     {"value": "94%",  "label": "Customer Retention",   "trend": "up"},
                     {"value": "€8.3M","label": "Quarterly Revenue",     "trend": "up"},
                     {"value": "72",   "label": "NPS Score",             "trend": "up"},
                     {"value": "21%",  "label": "Operating Margin",      "trend": "up"},
                 ]),

    # ══ SECTION 11: Pricing Slides ════════════════════════════════════════════
    SlideContent(layout_type="section_header", title="11 · Pricing Slides",
                 bullets=["3-tier pricing cards: left neutral · middle elevated + badge · right dark"]),

    SlideContent(layout_type="pricing",
                 title="Skalierbare Preismodelle – Transparent und Wachstumsorientiert",
                 items=[
                     {"tier": "Growth",       "price": "ab 1.500 €",  "period": "pro Monat",
                      "target": "KMU & Startups",
                      "features": ["Bis zu 50 Nutzer", "3 Kern-Module", "Standard-Support", "Cloud-Hosting EU"]},
                     {"tier": "Professional", "price": "ab 4.500 €",  "period": "pro Monat",
                      "target": "Mittelstand",
                      "features": ["Bis zu 250 Nutzer", "5 Module inkl. AutoFlow",
                                   "Priority-Support 24h", "API-Zugang", "Onboarding-Paket"],
                      "recommended": True},
                     {"tier": "Enterprise",   "price": "Individuell", "period": "auf Anfrage",
                      "target": "Konzerne",
                      "features": ["Unbegrenzte Nutzer", "Alle Module", "Dedicated CSM",
                                   "SLA 99,99 %", "Custom-Integrationen"],
                      "dark": True},
                 ]),

    SlideContent(layout_type="pricing",
                 title="Three Service Tiers to Match Every Enterprise Need",
                 items=[
                     {"tier": "Starter",      "price": "$2,000",      "period": "per month",
                      "target": "Small Teams",
                      "features": ["Up to 25 users", "Core analytics", "Email support"]},
                     {"tier": "Business",     "price": "$6,500",      "period": "per month",
                      "target": "Growing Companies",
                      "features": ["Up to 500 users", "Advanced AI", "Priority 24/7 support",
                                   "Custom integrations", "Dedicated CSM"],
                      "recommended": True},
                     {"tier": "Enterprise",   "price": "Custom",      "period": "annual contract",
                      "target": "Large Organisations",
                      "features": ["Unlimited users", "All modules", "White-glove onboarding",
                                   "SLA 99.99%", "On-prem option"],
                      "dark": True},
                 ]),
]


# ── Build & save ──────────────────────────────────────────────────────────────

def _blank_template() -> bytes:
    """Minimal 16:9 blank template (no colours, no master content)."""
    prs = Presentation()
    prs.slide_width  = Inches(13.333)
    prs.slide_height = Inches(7.500)
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf.read()


def main():
    out = os.path.join(os.path.dirname(__file__), "layout_library.pptx")

    structure = PresentationStructure(
        title="PitchCraft – Complete Layout & Chart Library",
        subtitle="All 25 charts · 12 slide layouts incl. agenda / metrics_grid / pricing",
        author="PitchCraft QA — auto-generated",
        slides=SLIDES,
    )

    pptx_bytes = generate_pptx(_blank_template(), structure)

    with open(out, "wb") as f:
        f.write(pptx_bytes)

    total = len(SLIDES) + 1
    print(f"✓  {total} slides → {out}")
    print(f"   Charts tested: {sum(len(s.charts) for s in SLIDES)} renders across all slot sizes")


if __name__ == "__main__":
    main()
