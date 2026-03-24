"""
Nifty 50 Ticker Dictionary — maps company names, abbreviations,
and common aliases to NSE symbols (e.g. "RELIANCE.NS").

Used by the NER extractor and stock-mention resolver.
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════
# Canonical Nifty 50 Alias → NSE Symbol Mapping
# ═══════════════════════════════════════════════════════

NIFTY50_TICKER_MAP: dict[str, str] = {
    # ── Reliance Industries ───────────────────────────
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "ril": "RELIANCE.NS",
    "reliance ind": "RELIANCE.NS",

    # ── TCS ───────────────────────────────────────────
    "tcs": "TCS.NS",
    "tata consultancy": "TCS.NS",
    "tata consultancy services": "TCS.NS",

    # ── HDFC Bank ─────────────────────────────────────
    "hdfc bank": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "hdfc": "HDFCBANK.NS",

    # ── Infosys ───────────────────────────────────────
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "infosys ltd": "INFY.NS",
    "infosys limited": "INFY.NS",

    # ── ICICI Bank ────────────────────────────────────
    "icici bank": "ICICIBANK.NS",
    "icicibank": "ICICIBANK.NS",
    "icici": "ICICIBANK.NS",

    # ── Hindustan Unilever ────────────────────────────
    "hindustan unilever": "HINDUNILVR.NS",
    "hul": "HINDUNILVR.NS",
    "hindunilvr": "HINDUNILVR.NS",
    "hindustan unilever limited": "HINDUNILVR.NS",

    # ── State Bank of India ───────────────────────────
    "sbi": "SBIN.NS",
    "state bank of india": "SBIN.NS",
    "sbin": "SBIN.NS",
    "state bank": "SBIN.NS",

    # ── Bharti Airtel ─────────────────────────────────
    "bharti airtel": "BHARTIARTL.NS",
    "airtel": "BHARTIARTL.NS",
    "bhartiartl": "BHARTIARTL.NS",

    # ── ITC ───────────────────────────────────────────
    "itc": "ITC.NS",
    "itc limited": "ITC.NS",

    # ── Kotak Mahindra Bank ───────────────────────────
    "kotak mahindra bank": "KOTAKBANK.NS",
    "kotak bank": "KOTAKBANK.NS",
    "kotak": "KOTAKBANK.NS",
    "kotakbank": "KOTAKBANK.NS",

    # ── Larsen & Toubro ───────────────────────────────
    "larsen & toubro": "LT.NS",
    "l&t": "LT.NS",
    "lt": "LT.NS",
    "larsen and toubro": "LT.NS",

    # ── HCL Technologies ─────────────────────────────
    "hcl technologies": "HCLTECH.NS",
    "hcl tech": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "hcl": "HCLTECH.NS",

    # ── Axis Bank ─────────────────────────────────────
    "axis bank": "AXISBANK.NS",
    "axisbank": "AXISBANK.NS",
    "axis": "AXISBANK.NS",

    # ── Asian Paints ──────────────────────────────────
    "asian paints": "ASIANPAINT.NS",
    "asianpaint": "ASIANPAINT.NS",
    "asian paint": "ASIANPAINT.NS",

    # ── Maruti Suzuki ─────────────────────────────────
    "maruti suzuki": "MARUTI.NS",
    "maruti": "MARUTI.NS",
    "maruti suzuki india": "MARUTI.NS",

    # ── Sun Pharmaceutical ────────────────────────────
    "sun pharma": "SUNPHARMA.NS",
    "sun pharmaceutical": "SUNPHARMA.NS",
    "sunpharma": "SUNPHARMA.NS",
    "sun pharmaceuticals": "SUNPHARMA.NS",

    # ── Titan Company ─────────────────────────────────
    "titan": "TITAN.NS",
    "titan company": "TITAN.NS",

    # ── Bajaj Finance ─────────────────────────────────
    "bajaj finance": "BAJFINANCE.NS",
    "bajfinance": "BAJFINANCE.NS",

    # ── Avenue Supermarts (DMart) ─────────────────────
    "dmart": "DMART.NS",
    "avenue supermarts": "DMART.NS",
    "d-mart": "DMART.NS",

    # ── Wipro ─────────────────────────────────────────
    "wipro": "WIPRO.NS",
    "wipro ltd": "WIPRO.NS",

    # ── UltraTech Cement ──────────────────────────────
    "ultratech cement": "ULTRACEMCO.NS",
    "ultratech": "ULTRACEMCO.NS",
    "ultracemco": "ULTRACEMCO.NS",

    # ── ONGC ──────────────────────────────────────────
    "ongc": "ONGC.NS",
    "oil and natural gas": "ONGC.NS",
    "oil & natural gas": "ONGC.NS",

    # ── NTPC ──────────────────────────────────────────
    "ntpc": "NTPC.NS",
    "ntpc limited": "NTPC.NS",

    # ── Tata Motors ───────────────────────────────────
    "tata motors": "TATAMOTORS.NS",
    "tatamotors": "TATAMOTORS.NS",

    # ── JSW Steel ─────────────────────────────────────
    "jsw steel": "JSWSTEEL.NS",
    "jswsteel": "JSWSTEEL.NS",
    "jsw": "JSWSTEEL.NS",

    # ── Power Grid ────────────────────────────────────
    "power grid": "POWERGRID.NS",
    "powergrid": "POWERGRID.NS",
    "power grid corporation": "POWERGRID.NS",

    # ── Mahindra & Mahindra ───────────────────────────
    "mahindra & mahindra": "M&M.NS",
    "mahindra and mahindra": "M&M.NS",
    "m&m": "M&M.NS",
    "mahindra": "M&M.NS",

    # ── Tata Steel ────────────────────────────────────
    "tata steel": "TATASTEEL.NS",
    "tatasteel": "TATASTEEL.NS",

    # ── Adani Enterprises ─────────────────────────────
    "adani enterprises": "ADANIENT.NS",
    "adanient": "ADANIENT.NS",
    "adani ent": "ADANIENT.NS",

    # ── Adani Ports ───────────────────────────────────
    "adani ports": "ADANIPORTS.NS",
    "adaniports": "ADANIPORTS.NS",
    "adani ports & sez": "ADANIPORTS.NS",

    # ── Bajaj Finserv ─────────────────────────────────
    "bajaj finserv": "BAJAJFINSV.NS",
    "bajajfinsv": "BAJAJFINSV.NS",

    # ── Coal India ────────────────────────────────────
    "coal india": "COALINDIA.NS",
    "coalindia": "COALINDIA.NS",

    # ── Tech Mahindra ─────────────────────────────────
    "tech mahindra": "TECHM.NS",
    "techm": "TECHM.NS",

    # ── HDFC Life Insurance ───────────────────────────
    "hdfc life": "HDFCLIFE.NS",
    "hdfclife": "HDFCLIFE.NS",
    "hdfc life insurance": "HDFCLIFE.NS",

    # ── SBI Life Insurance ────────────────────────────
    "sbi life": "SBILIFE.NS",
    "sbilife": "SBILIFE.NS",
    "sbi life insurance": "SBILIFE.NS",

    # ── Grasim Industries ─────────────────────────────
    "grasim": "GRASIM.NS",
    "grasim industries": "GRASIM.NS",

    # ── Divi's Laboratories ───────────────────────────
    "divis lab": "DIVISLAB.NS",
    "divi's laboratories": "DIVISLAB.NS",
    "divislab": "DIVISLAB.NS",
    "divis laboratories": "DIVISLAB.NS",

    # ── IndusInd Bank ─────────────────────────────────
    "indusind bank": "INDUSINDBK.NS",
    "indusindbk": "INDUSINDBK.NS",
    "indusind": "INDUSINDBK.NS",

    # ── BPCL ──────────────────────────────────────────
    "bpcl": "BPCL.NS",
    "bharat petroleum": "BPCL.NS",

    # ── Britannia ─────────────────────────────────────
    "britannia": "BRITANNIA.NS",
    "britannia industries": "BRITANNIA.NS",

    # ── Cipla ─────────────────────────────────────────
    "cipla": "CIPLA.NS",

    # ── Eicher Motors ─────────────────────────────────
    "eicher motors": "EICHERMOT.NS",
    "eicher": "EICHERMOT.NS",
    "eichermot": "EICHERMOT.NS",
    "royal enfield": "EICHERMOT.NS",

    # ── Nestle India ──────────────────────────────────
    "nestle india": "NESTLEIND.NS",
    "nestle": "NESTLEIND.NS",
    "nestleind": "NESTLEIND.NS",

    # ── Dr Reddy's Laboratories ───────────────────────
    "dr reddy": "DRREDDY.NS",
    "dr reddy's": "DRREDDY.NS",
    "dr reddys": "DRREDDY.NS",
    "drreddy": "DRREDDY.NS",

    # ── Apollo Hospitals ──────────────────────────────
    "apollo hospitals": "APOLLOHOSP.NS",
    "apollo": "APOLLOHOSP.NS",
    "apollohosp": "APOLLOHOSP.NS",

    # ── Tata Consumer Products ────────────────────────
    "tata consumer": "TATACONSUM.NS",
    "tata consumer products": "TATACONSUM.NS",
    "tataconsum": "TATACONSUM.NS",

    # ── Hero MotoCorp ─────────────────────────────────
    "hero motocorp": "HEROMOTOCO.NS",
    "hero moto": "HEROMOTOCO.NS",
    "heromotoco": "HEROMOTOCO.NS",
    "hero": "HEROMOTOCO.NS",

    # ── Hindalco Industries ───────────────────────────
    "hindalco": "HINDALCO.NS",
    "hindalco industries": "HINDALCO.NS",

    # ── Bajaj Auto ────────────────────────────────────
    "bajaj auto": "BAJAJ-AUTO.NS",
    "bajaj-auto": "BAJAJ-AUTO.NS",
    "bajaj": "BAJAJ-AUTO.NS",
}

# Build a reverse lookup: NSE symbol → primary company name
_SYMBOL_TO_NAME: dict[str, str] = {}
for _alias, _sym in NIFTY50_TICKER_MAP.items():
    if _sym not in _SYMBOL_TO_NAME:
        _SYMBOL_TO_NAME[_sym] = _alias.title()


def resolve_symbol(text: str) -> str | None:
    """
    Resolve a company mention string to its NSE symbol.

    Args:
        text: raw company name / abbreviation / ticker

    Returns:
        NSE symbol (e.g. "RELIANCE.NS") or None if unresolved
    """
    normalised = text.strip().lower()
    return NIFTY50_TICKER_MAP.get(normalised)


def get_all_aliases() -> list[str]:
    """Return all alias strings for use in spaCy EntityRuler patterns."""
    return list(NIFTY50_TICKER_MAP.keys())


def get_all_symbols() -> set[str]:
    """Return the set of unique NSE symbols."""
    return set(NIFTY50_TICKER_MAP.values())


def get_symbol_name(symbol: str) -> str | None:
    """Return the human-readable name for a symbol."""
    return _SYMBOL_TO_NAME.get(symbol)
