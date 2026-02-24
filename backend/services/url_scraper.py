"""
PitchCraft URL Scraper — Website Content & Image Extraction
=============================================================
Detects URLs in user prompts, scrapes text content and downloads images
for use in AI-generated presentations.

Limits:
  - Max 5 URLs per prompt
  - Max 10 images total
  - Max 5 MB per image
  - 10 s timeout per request
"""

# ============================================================================
# SECTION: Imports & Configuration
# ============================================================================

import logging
import re
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Limits ──────────────────────────────────────────────────────────────────
_MAX_URLS          = 5
_MAX_IMAGES        = 10
_MAX_IMAGE_BYTES   = 5 * 1024 * 1024  # 5 MB
_REQUEST_TIMEOUT   = 10               # seconds
_IMAGE_EXTENSIONS  = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
_USER_AGENT        = "PitchCraft/1.0 (presentation generator)"


# ============================================================================
# SECTION: URL Extraction
# ============================================================================

def extract_urls(text: str) -> list[str]:
    """
    Extract HTTP/HTTPS URLs from free-form text.

    Args:
        text: User prompt or any text potentially containing URLs.

    Returns:
        Deduplicated list of URLs (max _MAX_URLS).
    """
    pattern = r'https?://[^\s<>"\')\]},]+'
    urls = re.findall(pattern, text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        # Strip trailing punctuation that's likely not part of the URL
        url = url.rstrip(".,;:!?")
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique[:_MAX_URLS]


# ============================================================================
# SECTION: Web Scraping
# ============================================================================

def scrape_url(url: str) -> dict:
    """
    Fetch a web page and extract text content and image URLs.

    Args:
        url: Full HTTP/HTTPS URL to scrape.

    Returns:
        Dict with keys:
          - url       (str):       The original URL.
          - title     (str):       Page title.
          - text      (str):       Cleaned text content (max 5000 chars).
          - image_urls (list[str]): Absolute URLs of images found on the page.
    """
    try:
        resp = requests.get(
            url,
            timeout=_REQUEST_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
            allow_redirects=True,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return {"url": url, "title": "", "text": "", "image_urls": []}

    soup = BeautifulSoup(resp.text, "lxml")

    # ── Title ──────────────────────────────────────────────────────────────
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # ── Text content ───────────────────────────────────────────────────────
    # Remove script/style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text[:5000]

    # ── Images ─────────────────────────────────────────────────────────────
    image_urls: list[str] = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        abs_url = urljoin(url, src)
        parsed = urlparse(abs_url)
        ext = Path(parsed.path).suffix.lower()
        if ext in _IMAGE_EXTENSIONS and abs_url not in image_urls:
            image_urls.append(abs_url)

    return {
        "url": url,
        "title": title,
        "text": text,
        "image_urls": image_urls[:20],  # cap per page
    }


# ============================================================================
# SECTION: Image Download
# ============================================================================

def download_image(image_url: str, session_dir: Path) -> Optional[Path]:
    """
    Download a single image to a local directory.

    Args:
        image_url:   Absolute URL of the image.
        session_dir: Local directory to store downloaded images.

    Returns:
        Path to downloaded image, or None if download failed.
    """
    try:
        resp = requests.get(
            image_url,
            timeout=_REQUEST_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
            stream=True,
        )
        resp.raise_for_status()

        # Check content length
        content_length = int(resp.headers.get("content-length", 0))
        if content_length > _MAX_IMAGE_BYTES:
            logger.info("Skipping image (too large: %d bytes): %s", content_length, image_url)
            return None

        # Determine filename
        parsed = urlparse(image_url)
        ext = Path(parsed.path).suffix.lower() or ".jpg"
        if ext not in _IMAGE_EXTENSIONS:
            ext = ".jpg"
        filename = f"img_{hash(image_url) & 0xFFFFFFFF:08x}{ext}"
        filepath = session_dir / filename

        # Download
        size = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                size += len(chunk)
                if size > _MAX_IMAGE_BYTES:
                    f.close()
                    filepath.unlink(missing_ok=True)
                    return None
                f.write(chunk)

        logger.info("Downloaded image: %s → %s (%d bytes)", image_url, filepath.name, size)
        return filepath

    except Exception as exc:
        logger.warning("Failed to download image %s: %s", image_url, exc)
        return None


# ============================================================================
# SECTION: Main Orchestrator
# ============================================================================

def scrape_urls_from_prompt(
    prompt: str,
    session_dir: Optional[Path] = None,
) -> tuple[str, list[Path]]:
    """
    Extract URLs from a prompt, scrape content and download images.

    Args:
        prompt:      User prompt text potentially containing URLs.
        session_dir: Directory to store downloaded images. Created if None.

    Returns:
        Tuple of:
          - scraped_text (str):       Combined text from all scraped pages,
                                      formatted for AI consumption.
          - image_paths (list[Path]): Local paths to downloaded images.
    """
    urls = extract_urls(prompt)
    if not urls:
        return "", []

    if session_dir is None:
        session_dir = Path(tempfile.mkdtemp(prefix="pitchcraft_images_"))
    session_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Scraping %d URL(s) from prompt", len(urls))

    text_parts: list[str] = []
    all_image_paths: list[Path] = []
    total_images = 0

    for url in urls:
        data = scrape_url(url)

        if data["text"]:
            text_parts.append(
                f"--- Source: {data['title'] or data['url']} ---\n"
                f"URL: {data['url']}\n"
                f"{data['text']}\n"
            )

        # Download images (respect global limit)
        for img_url in data["image_urls"]:
            if total_images >= _MAX_IMAGES:
                break
            path = download_image(img_url, session_dir)
            if path:
                all_image_paths.append(path)
                total_images += 1

    scraped_text = "\n\n".join(text_parts)
    logger.info(
        "Scraping complete: %d page(s), %d chars text, %d image(s)",
        len(text_parts), len(scraped_text), len(all_image_paths),
    )
    return scraped_text, all_image_paths
