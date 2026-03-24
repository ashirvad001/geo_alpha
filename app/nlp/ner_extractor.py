"""
Stock mention extraction using spaCy NER + custom Nifty 50 ticker dictionary.

Combines:
1. spaCy EntityRuler with patterns from the ticker dictionary
2. Direct dictionary matching on tokenised text

Maps all detected company mentions to NSE symbols.
"""

from __future__ import annotations

import logging
import re

import spacy
from spacy.language import Language
from spacy.tokens import Span

from app.nlp.ticker_map import (
    NIFTY50_TICKER_MAP,
    get_all_aliases,
    resolve_symbol,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# Singleton NLP model
# ═══════════════════════════════════════════════════════

_nlp: Language | None = None


def _get_nlp() -> Language:
    """Load the spaCy model once and add the custom EntityRuler."""
    global _nlp
    if _nlp is not None:
        return _nlp

    try:
        _nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("Downloading spaCy en_core_web_sm model...")
        from spacy.cli import download
        download("en_core_web_sm")
        _nlp = spacy.load("en_core_web_sm")

    # ── Add EntityRuler for Nifty 50 companies ────────
    ruler = _nlp.add_pipe("entity_ruler", before="ner")
    patterns = []
    for alias in get_all_aliases():
        # Multi-word patterns
        tokens = alias.split()
        if len(tokens) == 1:
            patterns.append({"label": "ORG", "pattern": alias})
        else:
            patterns.append({
                "label": "ORG",
                "pattern": [{"LOWER": t.lower()} for t in tokens],
            })
    ruler.add_patterns(patterns)

    logger.info(f"spaCy model loaded with {len(patterns)} ticker patterns")
    return _nlp


# ═══════════════════════════════════════════════════════
# Extraction functions
# ═══════════════════════════════════════════════════════

def extract_stock_mentions(text: str) -> list[str]:
    """
    Extract Nifty 50 stock mentions from a text string.

    Combines spaCy NER with direct dictionary matching.

    Args:
        text: news article text (headline + body)

    Returns:
        Deduplicated list of NSE symbols (e.g. ["RELIANCE.NS", "TCS.NS"])
    """
    if not text or not text.strip():
        return []

    symbols: set[str] = set()

    # ── Method 1: spaCy NER ───────────────────────────
    nlp = _get_nlp()
    doc = nlp(text[:5000])  # Limit to avoid long processing

    for ent in doc.ents:
        if ent.label_ == "ORG":
            symbol = resolve_symbol(ent.text)
            if symbol:
                symbols.add(symbol)

    # ── Method 2: Direct dictionary scan ──────────────
    text_lower = text.lower()
    # Sort aliases by length (longest first) for greedy matching
    sorted_aliases = sorted(get_all_aliases(), key=len, reverse=True)

    for alias in sorted_aliases:
        if len(alias) < 3:
            # Skip very short aliases to avoid false positives
            continue
        # Word-boundary matching
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, text_lower):
            symbol = resolve_symbol(alias)
            if symbol:
                symbols.add(symbol)

    return sorted(symbols)


def extract_stock_mentions_batch(
    texts: list[str],
) -> list[list[str]]:
    """
    Batch extract stock mentions from multiple texts.

    Args:
        texts: list of article texts

    Returns:
        List of lists of NSE symbols
    """
    return [extract_stock_mentions(t) for t in texts]
