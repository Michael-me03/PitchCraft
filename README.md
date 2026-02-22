<br/>

<div align="center">

# ⚡ DeckForge

**AI-powered PowerPoint generator — drop a PDF, describe your deck, download boardroom-quality slides in seconds.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## What is DeckForge?

DeckForge converts any PDF, Markdown file, or plain text prompt into a polished `.pptx` presentation using GPT-4o as the presentation strategist and a custom chart + layout engine to render the result.

**The pipeline:**

```
PDF / Prompt  →  GPT-4o (JSON structure)  →  Chart Engine (PNG)  →  PPTX Generator  →  .pptx
```

The AI acts as a McKinsey-trained consultant — extracting real data, structuring a narrative arc, choosing the right chart type for every insight, and filling every slide with specific, numbered facts.

---

## Features

### AI Presentation Strategist
- Extracts real numeric data from uploaded PDFs and Markdown files
- Follows a mandatory narrative arc: **Context → Evidence → Insights → Actions**
- Enforces content density: every slide must have 3–4 substantive bullets or a real chart
- Detects your document's language and generates everything in that language (German, English, etc.)
- Asks targeted **clarifying questions** in the UI when context is missing or vague

### 25+ Chart Types via Three Rendering Engines

| Engine | Charts |
|--------|--------|
| **Plotly** | bar, grouped_bar, stacked_bar, line, multi_line, area, pie/donut, scatter, waterfall, funnel, treemap, sunburst, heatmap, radar, slope |
| **Matplotlib** | KPI card, multi-KPI row, gauge, progress ring, icon-stat grid |
| **Altair** | box plot, histogram, density plot |

### 14 Slide Layout Types
`title` · `agenda` · `section_header` · `content` · `chart` · `multi_chart` · `key_number` · `two_column` · `icon_grid` · `timeline` · `quote` · `metrics_grid` · `pricing` · `closing`

### Corporate Template Support
- Upload any `.pptx` as a template, or pick from the built-in catalog (20+ templates)
- Automatically uses **native slide layouts** from corporate templates (section dividers, two-column, statement/quote layouts)
- Preserves the template's fonts, colors, and watermarks — only fills in content

### Smart Clarification Flow
When you click **Review & Generate**, DeckForge checks whether your context is sufficient. If not, it surfaces 2–3 targeted questions inline — answer them or skip. Your answers are fed into the generation as high-priority context.

---

## Screenshots

<table>
  <tr>
    <td align="center"><b>Step 1 — Template Gallery</b></td>
    <td align="center"><b>Step 2 — Prompt & Upload</b></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/ui_step1.png" alt="Template Gallery" width="400"/></td>
    <td><img src="docs/screenshots/ui_step2.png" alt="Prompt Editor" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><b>Clarification Flow</b></td>
    <td align="center"><b>Generated Presentation</b></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/ui_clarify.png" alt="Clarification Panel" width="400"/></td>
    <td><img src="docs/screenshots/output_slide.png" alt="Output Slide" width="400"/></td>
  </tr>
</table>

### Chart Engine Previews

<table>
  <tr>
    <td><img src="docs/screenshots/kpi_card.png" width="180"/></td>
    <td><img src="docs/screenshots/bar_chart.png" width="180"/></td>
    <td><img src="docs/screenshots/line_chart.png" width="180"/></td>
    <td><img src="docs/screenshots/waterfall_chart.png" width="180"/></td>
  </tr>
  <tr>
    <td align="center">KPI Card</td>
    <td align="center">Bar Chart</td>
    <td align="center">Line Chart</td>
    <td align="center">Waterfall</td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/pie_chart.png" width="180"/></td>
    <td><img src="docs/screenshots/radar_chart.png" width="180"/></td>
    <td><img src="docs/screenshots/funnel_chart.png" width="180"/></td>
    <td><img src="docs/screenshots/heatmap_chart.png" width="180"/></td>
  </tr>
  <tr>
    <td align="center">Pie / Donut</td>
    <td align="center">Radar</td>
    <td align="center">Funnel</td>
    <td align="center">Heatmap</td>
  </tr>
</table>

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI + Uvicorn |
| AI Model | OpenAI GPT-4o (generation) + GPT-4o-mini (clarification check) |
| PPTX Engine | python-pptx |
| PDF Parsing | PyMuPDF (fitz) |
| Chart Rendering | Plotly/Kaleido · Matplotlib · Altair/vl-convert |
| Data Processing | Pandas · SciPy · Squarify |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite 6 |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| HTTP Client | Axios |
| Icons | Lucide React |

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone the repository

```bash
git clone https://github.com/Michael-me03/DeckForge.git
cd DeckForge
```

### 2. Set up the backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file with your API key
echo "OPENAI_API_KEY=sk-..." > .env

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Set up the frontend

```bash
cd frontend

npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## API Reference

### `GET /api/health`
Liveness probe.

```json
{ "status": "ok" }
```

---

### `GET /api/templates`
Returns the full template catalog.

```json
[
  {
    "id": "nagarro",
    "name": "Nagarro",
    "category": "Corporate",
    "description": "...",
    "colors": { "bg": "#FFFFFF", "accent": "#00B4D8", "text": "#0F172A", "muted": "#64748B" },
    "tags": ["corporate", "light"]
  }
]
```

---

### `POST /api/clarify`
Check if the provided context is sufficient; returns targeted clarifying questions if not.

**Request** (`multipart/form-data`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_prompt` | string | yes | Free-text description of the presentation |
| `purpose` | string | no | `business` / `school` / `scientific` (default: `business`) |
| `pdf_file` | file | no | Source document (`.pdf` or `.md`) |

**Response:**
```json
{
  "needs_clarification": true,
  "questions": [
    {
      "id": "q1",
      "question": "What is the main goal of this presentation?",
      "hint": "e.g. close a deal, inform stakeholders, request funding"
    }
  ]
}
```

---

### `POST /api/generate`
Main generation endpoint. Returns a download ID for the generated PPTX.

**Request** (`multipart/form-data`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | string | one of | ID from `/api/templates` |
| `template_file` | file | one of | Custom `.pptx` template upload |
| `user_prompt` | string | yes* | Free-text design instructions |
| `purpose` | string | no | `business` / `school` / `scientific` |
| `pdf_file` | file | no | Source document (`.pdf` or `.md`) |
| `clarifications` | string | no | JSON `{question: answer}` from clarify step |

*Required unless `pdf_file` is provided.

**Response:**
```json
{
  "download_id": "3f7a1b2c-...",
  "filename": "DeckForge_Nagarro_2026-02-22.pptx"
}
```

---

### `GET /api/download/{download_id}`
Download the generated PPTX. Files expire 30 minutes after generation.

---

## Project Structure

```
DeckForge/
├── backend/
│   ├── main.py                    # FastAPI entry point & API endpoints
│   ├── requirements.txt
│   ├── models/
│   │   └── schemas.py             # Pydantic models (PresentationStructure, SlideSpec, ...)
│   ├── services/
│   │   ├── ai_service.py          # GPT-4o prompt builder, generation & clarification
│   │   ├── chart_engine.py        # 25+ chart renderers (Plotly, Matplotlib, Altair)
│   │   ├── pdf_parser.py          # PyMuPDF text extraction
│   │   ├── pptx_generator.py      # Layout engine — 14 slide types, native template layouts
│   │   └── template_generator.py  # Template catalog & background injection
│   └── templates/                 # Built-in .pptx corporate templates (20+)
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # 3-step wizard with clarification flow
│   │   ├── components/
│   │   │   ├── TemplateGallery.tsx
│   │   │   ├── PromptEditor.tsx
│   │   │   └── ProgressIndicator.tsx
│   │   ├── styles/globals.css
│   │   └── types/template.ts
│   ├── package.json
│   └── vite.config.ts
│
├── test/
│   ├── generate_layout_library.py # Full reference PPTX — all 25 chart types
│   ├── test_charts.py             # Chart PNG previews
│   └── inspect_pptx.py            # PPTX structure inspector
│
└── docs/
    └── screenshots/               # Chart previews & UI screenshots
```

---

## How the AI Prompt Works

DeckForge uses a multi-layer prompting strategy:

1. **System prompt** — Role definition (McKinsey consultant), full chart schema, 26 design rules including:
   - Language matching (German in → German out)
   - Narrative arc (Context → Evidence → Insights → Actions)
   - Content density (min 3 bullets per content slide, no empty chart slides)
   - Chart diversity rules (which chart type to use for what)

2. **User message** — Assembled from:
   - Style/purpose instruction
   - Template style context (colors, tone hints, native layout availability)
   - Document text (up to 50,000 characters)
   - Clarification answers (if provided)

3. **Response format** — `json_object` mode, parsed into `PresentationStructure` (Pydantic model), then rendered slide-by-slide

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ⚡ by <a href="https://github.com/Michael-me03">Michael Meier</a> · Powered by OpenAI GPT-4o
</div>
