"""
RBI MPC Bulletin PDF Parser.

Downloads MPC resolution PDFs from RBI website, extracts key
macroeconomic indicators using PyPDF2 + regex, stores raw PDF
in MongoDB and parsed data in PostgreSQL.
"""

import io
import logging
import re
from datetime import datetime

import httpx
from PyPDF2 import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_mongo_db

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# Regex Patterns for RBI Data Extraction
# ═══════════════════════════════════════════════════════

PATTERNS = {
    "repo_rate": [
        re.compile(r"repo\s*rate\s*(?:at|to|of)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
        re.compile(r"policy\s*repo\s*rate\s*(?:at|to|of)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
    ],
    "reverse_repo_rate": [
        re.compile(r"reverse\s*repo\s*rate\s*(?:at|to|of)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
        re.compile(r"standing\s*deposit\s*facility\s*(?:\(SDF\))?\s*rate\s*(?:at|to|of)?\s*(\d+\.?\d*)", re.IGNORECASE),
    ],
    "cpi_yoy": [
        re.compile(r"CPI\s*(?:inflation|based)?\s*(?:at|to|of|was)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
        re.compile(r"consumer\s*price\s*(?:index)?\s*(?:inflation)?\s*(?:at|to|of|was)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
        re.compile(r"headline\s*inflation\s*(?:at|to|of|was)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
    ],
    "gdp_growth": [
        re.compile(r"GDP\s*growth\s*(?:at|to|of|was)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
        re.compile(r"real\s*GDP\s*(?:growth)?\s*(?:at|to|of|was)?\s*(\d+\.?\d*)\s*(?:per\s*cent|%)", re.IGNORECASE),
    ],
    "forex_reserves": [
        re.compile(r"foreign\s*exchange\s*reserves\s*(?:stood\s*at|at|of|were)?\s*(?:US\s*\$|USD)?\s*([\d,]+\.?\d*)\s*(?:billion|bn)", re.IGNORECASE),
        re.compile(r"forex\s*reserves\s*(?:at|of|stood\s*at)?\s*(?:US\s*\$|USD)?\s*([\d,]+\.?\d*)\s*(?:billion|bn)", re.IGNORECASE),
    ],
}


def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF using PyPDF2."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _parse_indicators(text_content: str) -> dict:
    """
    Apply regex patterns to extract RBI indicators from text.
    Returns a dict with keys matching rbi_indicators columns.
    """
    results: dict = {}

    for field, patterns in PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(text_content)
            if match:
                raw_value = match.group(1).replace(",", "")
                try:
                    value = float(raw_value)
                    # Forex reserves: convert billion USD to crores (approx)
                    if field == "forex_reserves":
                        value = value * 100  # rough billion-to-hundred-crore
                    results[field] = value
                except ValueError:
                    logger.warning(f"Could not parse {field} value: {raw_value}")
                break  # Use first matching pattern

    return results


async def download_rbi_bulletin(url: str | None = None) -> bytes | None:
    """
    Download the latest RBI MPC bulletin PDF.
    Returns raw PDF bytes, or None on failure.
    """
    target_url = url or settings.rbi_bulletin_url

    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    ) as client:
        try:
            response = await client.get(target_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "pdf" in content_type.lower():
                return response.content

            # If the page is HTML, try to find PDF links
            # This is a simplified approach; in production, you'd parse
            # the RBI bulletin page for the latest MPC resolution PDF
            logger.info("Response is HTML — attempting to find PDF links")
            pdf_links = re.findall(
                r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                response.text,
                re.IGNORECASE,
            )

            for link in pdf_links[:3]:  # Try first 3 PDF links
                if "mpc" in link.lower() or "monetary" in link.lower():
                    if not link.startswith("http"):
                        link = f"https://www.rbi.org.in{link}"
                    pdf_response = await client.get(link)
                    if pdf_response.status_code == 200:
                        return pdf_response.content

            logger.warning("No MPC PDF found on the bulletin page")
            return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading RBI bulletin: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading RBI bulletin: {e}")
            return None


async def parse_and_store_bulletin(
    db: AsyncSession,
    pdf_url: str | None = None,
) -> dict | None:
    """
    Full pipeline: download PDF → extract text → parse indicators →
    store raw PDF in MongoDB → insert parsed data into PostgreSQL.

    Returns parsed indicators dict or None on failure.
    """
    # 1. Download PDF
    pdf_bytes = await download_rbi_bulletin(pdf_url)
    if pdf_bytes is None:
        logger.warning("No PDF downloaded — skipping RBI parse")
        return None

    # 2. Extract text
    try:
        full_text = _extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return None

    if not full_text.strip():
        logger.warning("Extracted text is empty")
        return None

    # 3. Parse indicators
    indicators = _parse_indicators(full_text)
    logger.info(f"Parsed RBI indicators: {indicators}")

    if not indicators:
        logger.warning("No indicators could be extracted from the PDF")

    # 4. Store raw PDF + metadata in MongoDB
    mongo_db = get_mongo_db()
    await mongo_db.rbi_bulletins.insert_one({
        "downloaded_at": datetime.utcnow(),
        "source_url": pdf_url or settings.rbi_bulletin_url,
        "pdf_size_bytes": len(pdf_bytes),
        "pdf_data": pdf_bytes,
        "extracted_text_preview": full_text[:2000],
        "parsed_indicators": indicators,
        "status": "processed",
    })

    # Also add to NLP processing queue
    await mongo_db.nlp_queue.insert_one({
        "type": "rbi_bulletin",
        "text": full_text,
        "status": "pending",
        "created_at": datetime.utcnow(),
    })

    # 5. Insert into PostgreSQL rbi_indicators table
    if indicators:
        await db.execute(
            text("""
                INSERT INTO rbi_indicators (
                    ts, repo_rate, reverse_repo_rate, cpi_yoy,
                    gdp_growth, forex_reserves, indicator_source
                ) VALUES (
                    :ts, :repo_rate, :reverse_repo_rate, :cpi_yoy,
                    :gdp_growth, :forex_reserves, :indicator_source
                )
            """),
            {
                "ts": datetime.utcnow(),
                "repo_rate": indicators.get("repo_rate"),
                "reverse_repo_rate": indicators.get("reverse_repo_rate"),
                "cpi_yoy": indicators.get("cpi_yoy"),
                "gdp_growth": indicators.get("gdp_growth"),
                "forex_reserves": indicators.get("forex_reserves"),
                "indicator_source": pdf_url or settings.rbi_bulletin_url,
            },
        )
        await db.commit()
        logger.info("RBI indicators stored in PostgreSQL")

    return indicators
