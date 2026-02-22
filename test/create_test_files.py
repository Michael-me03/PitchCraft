"""Create test PDF and PPTX template for end-to-end testing."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

OUT_DIR = os.path.dirname(__file__)

# === Create Test PDF ===
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Helvetica", "B", 20)
pdf.cell(0, 15, "Q4 2025 Business Performance Report", ln=True, align="C")
pdf.set_font("Helvetica", "", 11)
pdf.ln(5)

content = """Executive Summary
TechCorp achieved record-breaking results in Q4 2025, with total revenue reaching $48.5 million, representing a 34% year-over-year growth. Operating margins improved to 22.4%, up from 18.1% in Q4 2024. The company added 1,250 new enterprise customers, bringing the total active customer base to 8,400.

Revenue Breakdown
- Cloud Services: $22.3M (46% of total revenue, up 52% YoY)
- Enterprise Licenses: $14.2M (29% of total, up 18% YoY)
- Professional Services: $8.1M (17% of total, up 28% YoY)
- Support & Maintenance: $3.9M (8% of total, up 12% YoY)

Key Performance Metrics
Monthly Recurring Revenue (MRR) grew to $16.2M, a 41% increase from Q4 2024. Customer acquisition cost (CAC) decreased by 15% to $2,400 per customer. Net Revenue Retention rate stands at 128%, indicating strong expansion within existing accounts. Average deal size increased to $58,000 from $45,000 in the previous year.

Market Position
TechCorp now holds 18% market share in the enterprise cloud solutions segment, up from 12% last year. Key competitors include CloudMax (24% share), DataPrime (15% share), and NetSolutions (11% share). Our Net Promoter Score improved to 72, ranking us first in customer satisfaction.

Regional Performance
- North America: $28.5M (59% of revenue, +30% YoY)
- Europe: $12.1M (25% of revenue, +42% YoY)
- Asia Pacific: $5.8M (12% of revenue, +55% YoY)
- Rest of World: $2.1M (4% of revenue, +25% YoY)

Product Development
Launched 3 major product updates in Q4: AI-powered analytics dashboard, real-time collaboration suite, and advanced security module. R&D investment was $8.2M (17% of revenue). Patent portfolio expanded to 45 active patents. Customer feature requests fulfillment rate improved to 78%.

Employee & Culture
Headcount grew to 620 employees, a 28% increase. Employee satisfaction score: 4.3/5. Voluntary turnover decreased to 8.2% from 12.1%. Diversity hiring improved: 45% of new hires from underrepresented groups.

Outlook for 2026
Projected revenue: $210M (full year), representing 35% growth. Planning to expand into 3 new markets. Targeting 12,000 active customers by year-end. R&D budget increasing to 20% of revenue to accelerate AI capabilities.
"""

for line in content.split('\n'):
    line = line.strip()
    if not line:
        pdf.ln(3)
        continue
    if line and not line.startswith('-') and len(line) < 60 and line[0].isupper():
        pdf.set_font("Helvetica", "B", 13)
        pdf.ln(3)
        pdf.cell(0, 8, line, ln=True)
        pdf.set_font("Helvetica", "", 11)
    elif line.startswith('-'):
        pdf.cell(10)
        pdf.cell(0, 7, line, ln=True)
    else:
        pdf.multi_cell(0, 6, line)

pdf.output(os.path.join(OUT_DIR, "test_report.pdf"))
print("Created test_report.pdf")


# === Create PPTX Template ===
prs = Presentation()
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

# We need to create proper slide layouts in the template
# The default template already has standard layouts, so let's customize them

# Save as template
prs.save(os.path.join(OUT_DIR, "test_template.pptx"))
print("Created test_template.pptx")
print("Done!")
