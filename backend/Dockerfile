FROM python:3.11-slim

WORKDIR /app

# System dependencies for Matplotlib / Plotly / Kaleido rendering
# Chromium is required by Kaleido >=1.x for Plotly PNG export
# LibreOffice Impress is required for PPTX → PDF preview conversion
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0t64 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    chromium \
    libreoffice-impress \
    libreoffice-common \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f -v

# Tell Kaleido / Plotly where Chromium lives
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_PATH=/usr/bin/chromium

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
