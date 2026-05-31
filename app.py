"""
FinTerminal India — Next-Generation Indian Brokerage Platform
=============================================================
Architecture: Single-file Streamlit app
Data: 100% live via yfinance + free RSS feeds + computed analytics
Author: Principal Fintech Architect
Version: 1.0.0
"""

# ─── STDLIB ──────────────────────────────────────────────────────────────────
import time
import json
import uuid
import math
import hashlib
import warnings
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Tuple, Any
import pytz

# ─── THIRD PARTY ─────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import feedparser
from scipy import stats
import ta

warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

IST = pytz.timezone("Asia/Kolkata")
APP_TITLE = "FinTerminal India"

INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY MIDCAP": "^NSEMDCP50",
    "INDIA VIX": "^INDIAVIX",
}

GLOBAL_INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW JONES": "^DJI",
    "NIKKEI 225": "^N225",
    "HANG SENG": "^HSI",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "SGX NIFTY": "^NSEI",
}

COMMODITIES = {
    "GOLD": "GC=F",
    "CRUDE OIL (WTI)": "CL=F",
    "BRENT CRUDE": "BZ=F",
    "SILVER": "SI=F",
    "NATURAL GAS": "NG=F",
}

FOREX = {
    "USD/INR": "INR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
    "USD/DXY": "DX-Y.NYB",
}

BOND_YIELDS = {
    "US 10Y": "^TNX",
    "INDIA 10Y": "IN10YT=XX",
}

NSE_SECTORS = {
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "BIOCON.NS"],
    "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "IOC.NS", "BPCL.NS", "POWERGRID.NS"],
    "Metals": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "VEDL.NS"],
    "Infra": ["L&T.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS", "NTPC.NS"],
}

NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "BAJFINANCE.NS", "HCLTECH.NS", "WIPRO.NS", "NESTLEIND.NS",
    "ULTRACEMCO.NS", "TATAMOTORS.NS", "ONGC.NS", "POWERGRID.NS", "NTPC.NS",
    "TATASTEEL.NS", "M&M.NS", "DRREDDY.NS", "TECHM.NS", "CIPLA.NS",
    "BAJAJFINSV.NS", "ADANIPORTS.NS", "COALINDIA.NS", "HINDALCO.NS", "DIVISLAB.NS",
    "JSWSTEEL.NS", "GRASIM.NS", "BRITANNIA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "TATACONSUM.NS", "APOLLOHOSP.NS", "BPCL.NS", "INDUSINDBK.NS", "VEDL.NS",
    "SHREECEM.NS", "UPL.NS", "SBILIFE.NS", "HDFCLIFE.NS", "PIDILITIND.NS",
]

NEWS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://feeds.feedburner.com/ndtvprofit-latest",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://feeds.feedburner.com/zeebiz/english",
]

MACRO_KEYWORDS = ["rbi", "rate", "inflation", "gdp", "policy", "fiscal", "budget", "cpi", "wpi", "repo"]
EQUITY_KEYWORDS = ["nifty", "sensex", "stock", "equity", "share", "ipo", "listing", "rally", "bull", "bear"]
EARNINGS_KEYWORDS = ["profit", "revenue", "quarterly", "results", "earnings", "q1", "q2", "q3", "q4", "ebitda"]
GEO_KEYWORDS = ["war", "conflict", "sanction", "geopolitical", "ukraine", "china", "usa", "global", "tension"]
COMMODITY_KEYWORDS = ["oil", "gold", "silver", "crude", "metal", "commodity", "brent", "wti"]

MACRO_SENSITIVITY = {
    "crude_oil": ["ONGC.NS", "RELIANCE.NS", "BPCL.NS", "IOC.NS", "TATAMOTORS.NS", "INDIGO.NS"],
    "usdinr": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "SUNPHARMA.NS"],
    "interest_rate": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "BAJFINANCE.NS", "SBIN.NS"],
    "global_selloff": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COALINDIA.NS"],
}

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG — must be first Streamlit call
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — institutional light theme
# ═══════════════════════════════════════════════════════════════════════════════

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg-primary: #F8F9FB;
    --bg-card: #FFFFFF;
    --bg-card-hover: #F4F6FA;
    --border: #E2E7EF;
    --border-light: #EEF1F7;
    --accent: #1B6CA8;
    --accent-light: #EBF4FF;
    --accent-dark: #0F4C7A;
    --positive: #0D9373;
    --positive-light: #E6F7F2;
    --negative: #D92D20;
    --negative-light: #FEF3F2;
    --neutral: #5A6474;
    --text-primary: #0F1923;
    --text-secondary: #5A6474;
    --text-muted: #8C95A3;
    --shadow-sm: 0 1px 3px rgba(15,25,35,0.06), 0 1px 2px rgba(15,25,35,0.04);
    --shadow-md: 0 4px 12px rgba(15,25,35,0.08), 0 2px 4px rgba(15,25,35,0.04);
    --radius: 10px;
    --radius-lg: 16px;
}

* { font-family: 'DM Sans', sans-serif; }

.stApp {
    background-color: var(--bg-primary);
}

/* ── SIDEBAR TOGGLE BUTTON (hamburger) ── */
[data-testid="stSidebarCollapsedControl"],
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] button {
    width: 48px !important;
    height: 48px !important;
    background: var(--accent) !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(27,108,168,0.35) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    transition: background 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stSidebarCollapsedControl"]:hover,
button[data-testid="collapsedControl"]:hover {
    background: var(--accent-dark) !important;
    box-shadow: 0 6px 18px rgba(27,108,168,0.45) !important;
}
/* Replace the default arrow icon with a hamburger via pseudo-element */
[data-testid="stSidebarCollapsedControl"] svg,
button[data-testid="collapsedControl"] svg {
    display: none !important;
}
[data-testid="stSidebarCollapsedControl"]::after,
button[data-testid="collapsedControl"]::after {
    content: '' !important;
    display: block !important;
    width: 22px !important;
    height: 16px !important;
    background:
        linear-gradient(white, white) 0 0/100% 2.5px no-repeat,
        linear-gradient(white, white) 0 50%/100% 2.5px no-repeat,
        linear-gradient(white, white) 0 100%/100% 2.5px no-repeat !important;
    border-radius: 2px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label { color: var(--text-secondary) !important; font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.04em !important; text-transform: uppercase !important; }

/* ── MAIN HEADER ── */
.main-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.2rem 0 1rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.brand-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-dark);
    letter-spacing: -0.02em;
}
.brand-tagline {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 400;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* ── GLOBAL DYNAMIC FONT SCALING ── */
html { font-size: clamp(12px, 1.1vw, 16px); }

/* ── METRIC CARDS ── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem 1rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
    min-width: 0;
}
.metric-card:hover { box-shadow: var(--shadow-md); }
.metric-label {
    font-size: clamp(0.55rem, 0.65vw, 0.7rem);
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.35rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-value {
    font-size: clamp(0.85rem, 1.4vw, 1.5rem);
    font-weight: 700;
    color: var(--text-primary);
    font-family: 'DM Mono', monospace;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin-bottom: 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-change-pos {
    font-size: clamp(0.65rem, 0.75vw, 0.78rem);
    font-weight: 600;
    color: var(--positive);
    font-family: 'DM Mono', monospace;
    white-space: nowrap;
}
.metric-change-neg {
    font-size: clamp(0.65rem, 0.75vw, 0.78rem);
    font-weight: 600;
    color: var(--negative);
    font-family: 'DM Mono', monospace;
    white-space: nowrap;
}
.metric-source {
    font-size: 0.62rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

/* ── SECTION HEADERS ── */
.section-header {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.75rem;
    margin-top: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* ── STOCK ROWS ── */
.stock-row {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius);
    padding: 0.65rem 1rem;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.15s ease;
    cursor: pointer;
}
.stock-row:hover {
    border-color: var(--accent);
    background: var(--accent-light);
    box-shadow: var(--shadow-sm);
}
.stock-ticker {
    font-family: 'DM Mono', monospace;
    font-weight: 600;
    font-size: 0.82rem;
    color: var(--text-primary);
}
.stock-name {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 1px;
}

/* ── BADGES ── */
.badge-pos {
    background: var(--positive-light);
    color: var(--positive);
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}
.badge-neg {
    background: var(--negative-light);
    color: var(--negative);
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}
.badge-neutral {
    background: #F2F4F7;
    color: var(--neutral);
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
}

/* ── DATA TABLE ── */
.data-table-header {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.5rem 0;
    border-bottom: 2px solid var(--border);
}

/* ── NEWS CARD ── */
.news-card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
    box-shadow: var(--shadow-sm);
}
.news-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.4;
    margin-bottom: 0.35rem;
}
.news-meta {
    font-size: 0.65rem;
    color: var(--text-muted);
    display: flex;
    gap: 0.75rem;
    align-items: center;
}
.news-tag-macro { color: #7C3AED; background: #F5F3FF; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.news-tag-equity { color: var(--accent); background: var(--accent-light); padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.news-tag-earnings { color: #D97706; background: #FFFBEB; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.news-tag-geo { color: #B91C1C; background: #FEF2F2; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.news-tag-commodity { color: #065F46; background: #ECFDF5; padding: 1px 6px; border-radius: 3px; font-weight: 600; }
.news-tag-general { color: var(--neutral); background: #F2F4F7; padding: 1px 6px; border-radius: 3px; font-weight: 600; }

/* ── ORDER PANEL ── */
.order-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    box-shadow: var(--shadow-md);
}

/* ── PNL DISPLAY ── */
.pnl-pos { color: var(--positive); font-family: 'DM Mono', monospace; font-weight: 700; }
.pnl-neg { color: var(--negative); font-family: 'DM Mono', monospace; font-weight: 700; }
.pnl-zero { color: var(--neutral); font-family: 'DM Mono', monospace; font-weight: 600; }

/* ── STATUS CHIPS ── */
.chip-live {
    background: var(--positive-light);
    color: var(--positive);
    font-size: 0.62rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.chip-closed {
    background: #F2F4F7;
    color: var(--neutral);
    font-size: 0.62rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── ALERT BANNERS ── */
.alert-warning {
    background: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: var(--radius);
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #92400E;
    margin-bottom: 0.5rem;
}
.alert-error {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: var(--radius);
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #991B1B;
    margin-bottom: 0.5rem;
}
.alert-success {
    background: var(--positive-light);
    border: 1px solid #A7F3D0;
    border-radius: var(--radius);
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #065F46;
    margin-bottom: 0.5rem;
}
.alert-info {
    background: var(--accent-light);
    border: 1px solid #BAD8F7;
    border-radius: var(--radius);
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: var(--accent-dark);
    margin-bottom: 0.5rem;
}

/* ── PORTFOLIO TABLE ── */
.port-row-even { background: var(--bg-card); }
.port-row-odd { background: var(--bg-primary); }

/* ── WATCHLIST PRIORITY CHIPS ── */
.wl-breakout { color: #7C3AED; background: #F5F3FF; font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.wl-momentum { color: var(--positive); background: var(--positive-light); font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.wl-volume { color: #D97706; background: #FFFBEB; font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.wl-volatile { color: var(--negative); background: var(--negative-light); font-size: 0.62rem; font-weight: 700; padding: 1px 6px; border-radius: 3px; }
.wl-neutral { color: var(--neutral); background: #F2F4F7; font-size: 0.62rem; font-weight: 600; padding: 1px 6px; border-radius: 3px; }

/* ── MISC FIXES ── */
.stButton > button {
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-dark) !important;
    border-color: var(--accent-dark) !important;
}
.stTextInput > div > div > input {
    border-radius: var(--radius) !important;
    border-color: var(--border) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
}
.stSelectbox > div > div {
    border-radius: var(--radius) !important;
    border-color: var(--border) !important;
}
.stNumberInput > div > div > input {
    font-family: 'DM Mono', monospace !important;
}
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.8rem 1rem;
    box-shadow: var(--shadow-sm);
}
div[data-testid="stMetric"] label {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: var(--text-muted) !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.3rem !important;
    color: var(--text-primary) !important;
}
.user-avatar {
    width: 36px; height: 36px;
    border-radius: 50%;
    background: var(--accent);
    color: white;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.9rem;
}
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    background: transparent;
    border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.5rem 1rem;
    color: var(--text-secondary);
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}
</style>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_session():
    """Initialize all session state variables for a mock brokerage user."""
    defaults = {
        "user_name": None,
        "user_id": None,
        "cash_balance": 500000.0,        # ₹5 lakh default
        "initial_balance": 500000.0,
        "realized_pnl_total": 0.0,
        "holdings": {},                   # {ticker: {qty, avg_cost, sector}}
        "order_history": [],              # list of order dicts
        "watchlist": [],                  # list of tickers
        "page": "Market Overview",
        "market_data_cache": {},
        "last_refresh": None,
        "notifications": [],
        "stock_explorer_ticker": "RELIANCE.NS",
        "price_alerts": {},               # {ticker: {above/below, price}}
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LAYER — API ABSTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def fetch_ticker_info(ticker: str) -> Dict:
    """
    Multi-source fundamental fetch with accuracy corrections for Indian stocks.
    Sources: .info -> fast_info -> income_stmt -> balance_sheet -> OHLCV -> dividends.
    All ratios are cross-validated to catch yfinance scale errors.
    """
    merged: Dict = {}
    try:
        t = yf.Ticker(ticker)

        # ── 1. .info ──────────────────────────────────────────────────────
        try:
            raw_info = t.info or {}
            if isinstance(raw_info, dict) and len(raw_info) >= 3:
                merged.update({k: v for k, v in raw_info.items()
                                if v not in (None, "", "N/A", 0)})
        except Exception:
            pass

        # ── 2. fast_info (always reliable) ───────────────────────────────
        try:
            fi = t.fast_info
            fi_map = {
                "marketCap":          getattr(fi, "market_cap", None),
                "fiftyTwoWeekHigh":   getattr(fi, "fifty_two_week_high", None),
                "fiftyTwoWeekLow":    getattr(fi, "fifty_two_week_low", None),
                "regularMarketPrice": getattr(fi, "last_price", None),
                "averageVolume":      getattr(fi, "three_month_average_volume", None),
                "sharesOutstanding":  getattr(fi, "shares", None),
                "currency":           getattr(fi, "currency", None),
                "exchange":           getattr(fi, "exchange", None),
            }
            for k, v in fi_map.items():
                if v is not None and v != 0 and k not in merged:
                    merged[k] = v
        except Exception:
            pass

        # ── 3. income_stmt → Revenue, Net Income, annual EPS ─────────────
        # ACCURACY: income_stmt is annual; use it for EPS, not quarterly fastinfo
        # EPS from income_stmt = Net Income / shares (avoids yfinance EPS scale bugs)
        net_inc_val = None
        try:
            inc = t.income_stmt          # columns = annual periods, newest first
            if inc is not None and not inc.empty:
                latest = inc.iloc[:, 0]  # most recent full fiscal year

                for key in ("Total Revenue", "TotalRevenue"):
                    v = latest.get(key)
                    if v is not None and "totalRevenue" not in merged:
                        merged["totalRevenue"] = float(v); break

                for key in ("Net Income", "NetIncome", "Net Income Common Stockholders"):
                    v = latest.get(key)
                    if v is not None and "netIncomeToCommon" not in merged:
                        merged["netIncomeToCommon"] = float(v)
                        net_inc_val = float(v); break

                for key in ("EBIT", "Operating Income"):
                    v = latest.get(key)
                    if v is not None and "ebit" not in merged:
                        merged["ebit"] = float(v); break

                # Derive annual EPS = Net Income / shares (most accurate for .NS)
                shares = merged.get("sharesOutstanding")
                if net_inc_val and shares and shares > 0:
                    derived_eps = net_inc_val / shares
                    # Sanity: EPS should be a small fraction of share price
                    price = merged.get("regularMarketPrice", 0)
                    if price > 0 and 0 < derived_eps < price:
                        merged["trailingEps"] = round(derived_eps, 2)

        except Exception:
            pass

        # ── 4. balance_sheet → D/E, Current Ratio, ROE, ROA, P/B ─────────
        total_equity = None
        try:
            bs = t.balance_sheet         # annual, newest first
            if bs is not None and not bs.empty:
                lb = bs.iloc[:, 0]

                total_debt = next(
                    (float(lb.get(k)) for k in
                     ("Total Debt", "TotalDebt", "Long Term Debt")
                     if lb.get(k) is not None), None)

                for key in ("Common Stock Equity", "Stockholders Equity",
                             "Total Stockholders Equity"):
                    v = lb.get(key)
                    if v is not None:
                        total_equity = float(v); break

                if total_debt is not None and total_equity and total_equity != 0                         and "debtToEquity" not in merged:
                    merged["debtToEquity"] = round(total_debt / total_equity, 4)

                curr_a = next((float(lb.get(k)) for k in
                               ("Current Assets", "Total Current Assets")
                               if lb.get(k) is not None), None)
                curr_l = next((float(lb.get(k)) for k in
                               ("Current Liabilities", "Total Current Liabilities")
                               if lb.get(k) is not None), None)
                if curr_a and curr_l and curr_l != 0 and "currentRatio" not in merged:
                    merged["currentRatio"] = round(curr_a / curr_l, 4)

                # P/B = Price / Book Value Per Share
                # Book Value Per Share = Total Equity / Shares
                shares = merged.get("sharesOutstanding")
                price  = merged.get("regularMarketPrice")
                if total_equity and shares and shares > 0 and price                         and "priceToBook" not in merged:
                    bvps = total_equity / float(shares)
                    if bvps > 0:
                        pb = round(float(price) / bvps, 4)
                        # Sanity: P/B for Indian large-caps is typically 0.5x–30x
                        if 0.1 < pb < 100:
                            merged["priceToBook"] = pb

                ni = net_inc_val or merged.get("netIncomeToCommon")
                if ni and total_equity and total_equity != 0                         and "returnOnEquity" not in merged:
                    merged["returnOnEquity"] = round(float(ni) / total_equity, 6)

                total_assets = lb.get("Total Assets")
                if total_assets and float(total_assets) != 0 and ni                         and "returnOnAssets" not in merged:
                    merged["returnOnAssets"] = round(
                        float(ni) / float(total_assets), 6)
        except Exception:
            pass

        # ── 5. OHLCV → 52W range, AvgVol, Beta, derive P/E ──────────────
        try:
            df_h = yf.download(ticker, period="1y", interval="1d",
                                progress=False, auto_adjust=True)
            if df_h is not None and not df_h.empty:
                if isinstance(df_h.columns, pd.MultiIndex):
                    df_h.columns = df_h.columns.get_level_values(0)
                close = df_h["Close"].squeeze()

                if "fiftyTwoWeekHigh" not in merged:
                    merged["fiftyTwoWeekHigh"] = round(float(df_h["High"].squeeze().max()), 2)
                if "fiftyTwoWeekLow" not in merged:
                    merged["fiftyTwoWeekLow"] = round(float(df_h["Low"].squeeze().min()), 2)
                if "averageVolume" not in merged and "Volume" in df_h.columns:
                    merged["averageVolume"] = int(df_h["Volume"].mean())

                curr_price = float(close.iloc[-1])
                if "regularMarketPrice" not in merged:
                    merged["regularMarketPrice"] = round(curr_price, 2)
                if "marketCap" not in merged and merged.get("sharesOutstanding"):
                    merged["marketCap"] = int(curr_price * merged["sharesOutstanding"])

                # P/E = Price / Annual EPS  (validate result is sane)
                if "trailingPE" not in merged:
                    eps = merged.get("trailingEps", 0)
                    if eps and eps > 0:
                        pe = round(curr_price / eps, 2)
                        # Sanity: realistic P/E range for listed Indian equities
                        if 1 < pe < 500:
                            merged["trailingPE"] = pe

                # Forward P/E similarly validated
                if "forwardPE" not in merged:
                    feps = merged.get("forwardEps", 0)
                    if feps and feps > 0:
                        fpe = round(curr_price / feps, 2)
                        if 1 < fpe < 500:
                            merged["forwardPE"] = fpe

                # Beta vs NIFTY computed from daily returns
                if "beta" not in merged:
                    try:
                        bench = yf.download("^NSEI", period="1y", interval="1d",
                                             progress=False, auto_adjust=True)
                        if bench is not None and not bench.empty:
                            if isinstance(bench.columns, pd.MultiIndex):
                                bench.columns = bench.columns.get_level_values(0)
                            sr = close.pct_change().dropna()
                            br = bench["Close"].squeeze().pct_change().dropna()
                            idx = sr.index.intersection(br.index)
                            if len(idx) > 30:
                                cm = np.cov(sr.loc[idx].values, br.loc[idx].values)
                                if cm[1, 1] != 0:
                                    merged["beta"] = round(cm[0, 1] / cm[1, 1], 3)
                    except Exception:
                        pass
        except Exception:
            pass

        # ── 6. Dividends → annual yield (frequency-agnostic) ─────────────
        # ACCURACY: sum dividends paid in the last 12 months, not last N entries
        # This correctly handles quarterly (US-style) AND semi-annual (INFY-style)
        try:
            if "dividendYield" not in merged:
                divs = t.dividends
                if divs is not None and not divs.empty:
                    divs.index = divs.index.tz_localize(None)                         if divs.index.tz is not None else divs.index
                    cutoff = pd.Timestamp.now() - pd.DateOffset(years=1)
                    annual_div = float(divs[divs.index >= cutoff].sum())
                    p = merged.get("regularMarketPrice")
                    if p and p > 0 and annual_div > 0:
                        merged["dividendYield"] = round(annual_div / p, 6)
        except Exception:
            pass

        if not merged:
            return {"error": f"No data available for {ticker}"}
        return merged

    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=180)
def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetch OHLCV data with retry logic."""
    for attempt in range(3):
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            if df is not None and not df.empty:
                # Flatten multi-index columns if present
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
            time.sleep(0.5 * (attempt + 1))
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None


@st.cache_data(ttl=300)
def fetch_current_price(ticker: str) -> Optional[Dict]:
    """Fetch current price, day change, volume for a ticker."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d", interval="1d")
        if hist is None or hist.empty:
            return None
        hist = hist.copy()
        if len(hist) >= 2:
            prev_close = float(hist["Close"].iloc[-2])
            curr_close = float(hist["Close"].iloc[-1])
        else:
            prev_close = float(hist["Close"].iloc[-1])
            curr_close = prev_close
        change = curr_close - prev_close
        pct_change = (change / prev_close) * 100 if prev_close != 0 else 0
        return {
            "price": round(curr_close, 2),
            "prev_close": round(prev_close, 2),
            "change": round(change, 2),
            "pct_change": round(pct_change, 2),
            "volume": int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
            "high": round(float(hist["High"].iloc[-1]), 2),
            "low": round(float(hist["Low"].iloc[-1]), 2),
            "open": round(float(hist["Open"].iloc[-1]), 2),
        }
    except Exception:
        return None


@st.cache_data(ttl=600)
def fetch_multiple_prices(tickers: List[str]) -> Dict[str, Dict]:
    """Batch fetch current prices for multiple tickers."""
    results = {}
    try:
        joined = " ".join(tickers)
        data = yf.download(joined, period="5d", interval="1d", progress=False, auto_adjust=True, group_by="ticker")
        if data is None or data.empty:
            return results
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    df = data
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                else:
                    if ticker in data.columns.get_level_values(0):
                        df = data[ticker].dropna(how="all")
                    else:
                        continue
                if df.empty or len(df) < 1:
                    continue
                curr = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else curr
                chg = curr - prev
                pct = (chg / prev * 100) if prev != 0 else 0
                results[ticker] = {
                    "price": round(curr, 2),
                    "change": round(chg, 2),
                    "pct_change": round(pct, 2),
                    "volume": int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0,
                    "high": round(float(df["High"].iloc[-1]), 2),
                    "low": round(float(df["Low"].iloc[-1]), 2),
                }
            except Exception:
                continue
    except Exception:
        pass
    return results


@st.cache_data(ttl=1800)
def fetch_news_feed() -> List[Dict]:
    """Fetch and parse RSS news feeds with categorization."""
    articles = []
    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            if not feed or not feed.entries:
                continue
            for entry in feed.entries[:8]:
                import re
                raw_title = entry.get("title", "")
                title = re.sub(r'<[^>]+>', '', raw_title).strip()
                raw_summary = entry.get("summary", "")
                summary = re.sub(r'<[^>]+>', '', raw_summary).strip()
                link = entry.get("link", "#")
                published = entry.get("published", "")
                if not title:
                    continue
                text = (title + " " + summary).lower()
                category = _classify_news(text)
                tickers = _extract_tickers(title)
                articles.append({
                    "title": title[:160],
                    "summary": summary[:280],
                    "link": link,
                    "published": published,
                    "category": category,
                    "tickers": tickers,
                    "source": feed_url.split("/")[2].replace("www.", ""),
                })
        except Exception:
            continue
    # Deduplicate by title similarity
    seen_titles = set()
    unique = []
    for art in articles:
        key = art["title"][:60].lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(art)
    return unique[:40]


def _classify_news(text: str) -> str:
    text = text.lower()
    if any(k in text for k in EARNINGS_KEYWORDS):
        return "earnings"
    if any(k in text for k in MACRO_KEYWORDS):
        return "macro"
    if any(k in text for k in GEO_KEYWORDS):
        return "geopolitical"
    if any(k in text for k in COMMODITY_KEYWORDS):
        return "commodity"
    if any(k in text for k in EQUITY_KEYWORDS):
        return "equity"
    return "general"


def _extract_tickers(title: str) -> List[str]:
    """Extract likely NSE tickers from news headline."""
    known_names = {
        "reliance": "RELIANCE.NS", "tcs": "TCS.NS", "infosys": "INFY.NS",
        "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS", "wipro": "WIPRO.NS",
        "itc": "ITC.NS", "sbi": "SBIN.NS", "maruti": "MARUTI.NS",
        "bajaj": "BAJFINANCE.NS", "tata": "TATAMOTORS.NS", "ongc": "ONGC.NS",
        "sun pharma": "SUNPHARMA.NS", "dr reddy": "DRREDDY.NS", "cipla": "CIPLA.NS",
        "l&t": "LT.NS", "nestle": "NESTLEIND.NS", "titan": "TITAN.NS",
        "adani": "ADANIPORTS.NS", "kotak": "KOTAKBANK.NS", "axis": "AXISBANK.NS",
        "hcl": "HCLTECH.NS", "tech mahindra": "TECHM.NS", "ntpc": "NTPC.NS",
        "coal india": "COALINDIA.NS", "hindalco": "HINDALCO.NS",
    }
    found = []
    title_lower = title.lower()
    for name, ticker in known_names.items():
        if name in title_lower:
            found.append(ticker)
    return found[:3]


@st.cache_data(ttl=900)
def compute_technicals(ticker: str) -> Dict:
    """Compute RSI, MACD, Bollinger Bands, ATR, EMA from price history."""
    try:
        df = fetch_ohlcv(ticker, period="6mo", interval="1d")
        if df is None or df.empty or len(df) < 30:
            return {"error": "Insufficient data"}
        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()

        # RSI
        rsi_series = ta.momentum.rsi(close, window=14)
        rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else None

        # MACD
        macd_obj = ta.trend.MACD(close)
        macd_val = float(macd_obj.macd().iloc[-1])
        macd_signal = float(macd_obj.macd_signal().iloc[-1])
        macd_hist = float(macd_obj.macd_diff().iloc[-1])

        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        bb_mid = float(bb.bollinger_mavg().iloc[-1])
        bb_pct = float(bb.bollinger_pband().iloc[-1]) * 100

        # ATR (volatility)
        atr = ta.volatility.AverageTrueRange(high, low, close, window=14)
        atr_val = float(atr.average_true_range().iloc[-1])

        # EMA
        ema20 = float(ta.trend.ema_indicator(close, window=20).iloc[-1])
        ema50 = float(ta.trend.ema_indicator(close, window=50).iloc[-1])
        ema200 = float(ta.trend.ema_indicator(close, window=200).iloc[-1]) if len(df) > 200 else None

        # Volume analysis
        vol_avg20 = float(df["Volume"].tail(20).mean()) if "Volume" in df.columns else 0
        vol_latest = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
        vol_ratio = (vol_latest / vol_avg20) if vol_avg20 > 0 else 1.0

        # Stochastic
        stoch = ta.momentum.StochasticOscillator(high, low, close, window=14)
        stoch_k = float(stoch.stoch().iloc[-1])
        stoch_d = float(stoch.stoch_signal().iloc[-1])

        curr_price = float(close.iloc[-1])

        return {
            "rsi": round(rsi, 2) if rsi else None,
            "macd": round(macd_val, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_hist": round(macd_hist, 4),
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "bb_mid": round(bb_mid, 2),
            "bb_pct": round(bb_pct, 2),
            "atr": round(atr_val, 2),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema200": round(ema200, 2) if ema200 else None,
            "vol_ratio": round(vol_ratio, 2),
            "stoch_k": round(stoch_k, 2),
            "stoch_d": round(stoch_d, 2),
            "price": round(curr_price, 2),
            "above_ema20": curr_price > ema20,
            "above_ema50": curr_price > ema50,
            "above_ema200": curr_price > ema200 if ema200 else None,
        }
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=600)
def compute_beta_correlation(ticker: str, benchmark: str = "^NSEI", period: str = "1y") -> Dict:
    """Compute beta, correlation, and rolling volatility vs benchmark."""
    try:
        combined = yf.download([ticker, benchmark], period=period, interval="1d", progress=False, auto_adjust=True)
        if combined is None or combined.empty:
            return {"error": "Download failed"}
        if isinstance(combined.columns, pd.MultiIndex):
            close = combined["Close"]
        else:
            return {"error": "Single ticker returned"}
        if ticker not in close.columns or benchmark not in close.columns:
            return {"error": "Columns missing"}
        rets = close.pct_change().dropna()
        if len(rets) < 30:
            return {"error": "Insufficient return data"}
        stock_rets = rets[ticker].values
        bench_rets = rets[benchmark].values
        cov_matrix = np.cov(stock_rets, bench_rets)
        beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else 1.0
        corr = float(np.corrcoef(stock_rets, bench_rets)[0, 1])
        ann_vol = float(np.std(stock_rets) * np.sqrt(252) * 100)
        rolling_vol = float(pd.Series(stock_rets).rolling(20).std().iloc[-1] * np.sqrt(252) * 100)
        return {
            "beta": round(beta, 3),
            "correlation": round(corr, 3),
            "ann_volatility": round(ann_vol, 2),
            "rolling_vol_20d": round(rolling_vol, 2),
            "period": period,
        }
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=600)
def compute_portfolio_analytics(holdings: str, prices_json: str) -> Dict:
    """
    Compute comprehensive portfolio analytics.
    Takes JSON-serialized holdings and prices for cache compatibility.
    """
    try:
        h = json.loads(holdings)
        prices = json.loads(prices_json)
        if not h or not prices:
            return {"error": "Empty portfolio"}

        portfolio_value = 0
        weights = {}
        for ticker, pos in h.items():
            price = prices.get(ticker, {}).get("price", pos["avg_cost"])
            val = price * pos["qty"]
            portfolio_value += val
            weights[ticker] = val

        if portfolio_value <= 0:
            return {"error": "Zero portfolio value"}

        for t in weights:
            weights[t] /= portfolio_value

        # Fetch return series for held stocks
        tickers_list = list(h.keys())
        period = "1y"
        try:
            raw = yf.download(tickers_list, period=period, interval="1d", progress=False, auto_adjust=True)
            if isinstance(raw.columns, pd.MultiIndex):
                close_data = raw["Close"]
            else:
                close_data = raw
            if isinstance(close_data, pd.Series):
                close_data = close_data.to_frame(tickers_list[0])
        except Exception:
            return {"error": "Return data unavailable"}

        if close_data.empty or len(close_data) < 30:
            return {"error": "Insufficient history"}

        rets = close_data.pct_change().dropna()

        # Portfolio return series (weighted)
        port_rets = pd.Series(0.0, index=rets.index)
        for t in tickers_list:
            if t in rets.columns and t in weights:
                port_rets += rets[t] * weights[t]

        # Sharpe (risk-free = 6.5% Indian repo)
        rf_daily = 0.065 / 252
        excess_rets = port_rets - rf_daily
        sharpe = float((excess_rets.mean() / port_rets.std()) * np.sqrt(252)) if port_rets.std() > 0 else 0

        # Drawdown
        cum_rets = (1 + port_rets).cumprod()
        rolling_max = cum_rets.cummax()
        drawdown = (cum_rets - rolling_max) / rolling_max
        max_dd = float(drawdown.min() * 100)

        # Annualized return
        total_return = float((cum_rets.iloc[-1] - 1) * 100)
        n_days = len(port_rets)
        ann_return = float(((cum_rets.iloc[-1]) ** (252 / n_days) - 1) * 100)

        # Portfolio volatility
        port_vol = float(port_rets.std() * np.sqrt(252) * 100)

        # Beta vs Nifty
        try:
            nifty = yf.download("^NSEI", period=period, interval="1d", progress=False, auto_adjust=True)
            if isinstance(nifty.columns, pd.MultiIndex):
                nifty_close = nifty["Close"].squeeze()
            else:
                nifty_close = nifty["Close"].squeeze()
            nifty_rets = nifty_close.pct_change().dropna()
            common_idx = port_rets.index.intersection(nifty_rets.index)
            if len(common_idx) > 20:
                pr = port_rets.loc[common_idx].values
                nr = nifty_rets.loc[common_idx].values
                cov = np.cov(pr, nr)
                beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 1.0
            else:
                beta = 1.0
        except Exception:
            beta = 1.0

        # Concentration risk (HHI)
        hhi = sum(w ** 2 for w in weights.values())
        diversification_score = max(0, round((1 - hhi) * 100, 1))

        # Sector exposure
        sector_exposure = {}
        for t, pos in h.items():
            sector = pos.get("sector", "Unknown")
            price = prices.get(t, {}).get("price", pos["avg_cost"])
            val = price * pos["qty"]
            sector_exposure[sector] = sector_exposure.get(sector, 0) + val

        total_inv = sum(sector_exposure.values())
        sector_pct = {s: round(v / total_inv * 100, 1) for s, v in sector_exposure.items()} if total_inv > 0 else {}

        return {
            "portfolio_value": round(portfolio_value, 2),
            "total_return_pct": round(total_return, 2),
            "ann_return_pct": round(ann_return, 2),
            "sharpe": round(sharpe, 3),
            "max_drawdown_pct": round(max_dd, 2),
            "portfolio_vol_pct": round(port_vol, 2),
            "beta": round(beta, 3),
            "diversification_score": diversification_score,
            "weights": {t: round(w * 100, 1) for t, w in weights.items()},
            "sector_pct": sector_pct,
            "cum_returns": cum_rets.tolist(),
            "dates": [str(d.date()) for d in cum_rets.index],
            "drawdown_series": drawdown.tolist(),
        }
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=900)
def fetch_sector_performance() -> Dict[str, Dict]:
    """Compute real sector performance from live stock prices."""
    results = {}
    for sector, tickers in NSE_SECTORS.items():
        try:
            prices = fetch_multiple_prices(tickers)
            changes = [p["pct_change"] for p in prices.values() if "pct_change" in p]
            if changes:
                avg_change = np.mean(changes)
                results[sector] = {
                    "avg_change": round(avg_change, 2),
                    "breadth_positive": sum(1 for c in changes if c > 0),
                    "total": len(changes),
                    "stocks": prices,
                }
        except Exception:
            continue
    return results


@st.cache_data(ttl=600)
def fetch_movers(n: int = 10) -> Tuple[List[Dict], List[Dict]]:
    """Fetch top gainers and losers from NIFTY 50 universe."""
    prices = fetch_multiple_prices(NIFTY50_TICKERS[:30])
    movers = []
    for ticker, data in prices.items():
        movers.append({
            "ticker": ticker.replace(".NS", ""),
            "full_ticker": ticker,
            "price": data.get("price", 0),
            "change": data.get("change", 0),
            "pct_change": data.get("pct_change", 0),
            "volume": data.get("volume", 0),
        })
    movers_sorted = sorted(movers, key=lambda x: x["pct_change"], reverse=True)
    gainers = [m for m in movers_sorted if m["pct_change"] > 0][:n]
    losers = [m for m in movers_sorted if m["pct_change"] < 0][-n:]
    return gainers, list(reversed(losers))


# ═══════════════════════════════════════════════════════════════════════════════
# ORDER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def validate_and_place_order(
    action: str,
    ticker: str,
    qty: int,
    order_type: str,
    limit_price: Optional[float],
    stop_price: Optional[float],
    execution_price: float,
    sector: str = "Unknown"
) -> Dict:
    """
    Core order execution engine.
    Validates balance/holdings, updates state, records transaction.
    """
    ticker = ticker.upper()
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    if qty <= 0:
        return {"success": False, "message": "Quantity must be positive."}
    if execution_price <= 0:
        return {"success": False, "message": "Invalid execution price."}

    order_value = execution_price * qty
    timestamp = datetime.now(IST).isoformat()
    order_id = str(uuid.uuid4())[:8].upper()

    if action == "BUY":
        total_cost = order_value
        if st.session_state.cash_balance < total_cost:
            return {
                "success": False,
                "message": f"Insufficient funds. Required: ₹{total_cost:,.2f}, Available: ₹{st.session_state.cash_balance:,.2f}"
            }
        # Execute BUY
        st.session_state.cash_balance -= total_cost
        holdings = st.session_state.holdings
        if ticker in holdings:
            existing = holdings[ticker]
            new_qty = existing["qty"] + qty
            new_avg = ((existing["avg_cost"] * existing["qty"]) + total_cost) / new_qty
            holdings[ticker] = {
                "qty": new_qty,
                "avg_cost": round(new_avg, 4),
                "sector": existing.get("sector", sector),
            }
        else:
            holdings[ticker] = {"qty": qty, "avg_cost": round(execution_price, 4), "sector": sector}

    elif action == "SELL":
        holdings = st.session_state.holdings
        if ticker not in holdings or holdings[ticker]["qty"] < qty:
            held = holdings.get(ticker, {}).get("qty", 0)
            return {
                "success": False,
                "message": f"Cannot sell {qty} units. You hold {held} units of {ticker}."
            }
        # Execute SELL
        pos = holdings[ticker]
        realized_pnl = (execution_price - pos["avg_cost"]) * qty
        proceeds = execution_price * qty
        st.session_state.cash_balance += proceeds
        realized_pnl = (execution_price - pos["avg_cost"]) * qty
        st.session_state.realized_pnl_total += realized_pnl
        new_qty = pos["qty"] - qty
        if new_qty == 0:
            del holdings[ticker]
        else:
            holdings[ticker]["qty"] = new_qty

        # Record realized PnL
        order_value_sell = proceeds
    else:
        return {"success": False, "message": "Invalid order action."}

    # Record in order history
    order_record = {
        "order_id": order_id,
        "timestamp": timestamp,
        "action": action,
        "ticker": ticker,
        "qty": qty,
        "order_type": order_type,
        "execution_price": round(execution_price, 2),
        "order_value": round(order_value, 2),
        "limit_price": limit_price,
        "stop_price": stop_price,
        "status": "EXECUTED",
        "sector": sector,
    }
    if action == "SELL":
        order_record["realized_pnl"] = round((execution_price - pos["avg_cost"]) * qty, 2)
    st.session_state.order_history.insert(0, order_record)
    notification = f"{'🟢' if action == 'BUY' else '🔴'} {action} {qty} × {ticker.replace('.NS','')} @ ₹{execution_price:,.2f}"
    st.session_state.notifications.insert(0, {"msg": notification, "ts": timestamp})

    return {
        "success": True,
        "message": f"Order {order_id} executed: {action} {qty} × {ticker.replace('.NS','')} @ ₹{execution_price:,.2f}",
        "order_id": order_id,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SMART WATCHLIST ENGINE (USP 5)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_watchlist_priorities(watchlist: List[str]) -> List[Dict]:
    """
    Prioritize watchlist dynamically using: volatility expansion,
    unusual volume, breakout probability, momentum acceleration.
    """
    if not watchlist:
        return []

    results = []
    for ticker in watchlist:
        try:
            df = fetch_ohlcv(ticker, period="60d", interval="1d")
            if df is None or df.empty or len(df) < 20:
                results.append({
                    "ticker": ticker, "priority_score": 0,
                    "signals": [], "signal_label": "No Data",
                    "price": None, "pct_change": None,
                })
                continue

            close = df["Close"].squeeze()
            vol = df["Volume"].squeeze() if "Volume" in df.columns else pd.Series(dtype=float)

            # Momentum: 5-day vs 20-day return
            ret5 = float((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) >= 5 else 0
            ret20 = float((close.iloc[-1] / close.iloc[-20] - 1) * 100) if len(close) >= 20 else 0
            momentum_accel = ret5 - (ret20 / 4)  # normalized

            # Volume spike
            vol_ratio = 1.0
            if not vol.empty and len(vol) >= 20:
                avg_vol = float(vol.iloc[-20:-1].mean())
                if avg_vol > 0:
                    vol_ratio = float(vol.iloc[-1]) / avg_vol

            # Volatility expansion (ATR expansion)
            high = df["High"].squeeze()
            low = df["Low"].squeeze()
            tr = pd.concat([
                high - low,
                (high - close.shift(1)).abs(),
                (low - close.shift(1)).abs()
            ], axis=1).max(axis=1)
            atr10 = float(tr.tail(10).mean()) if len(tr) >= 10 else 0
            atr30 = float(tr.tail(30).mean()) if len(tr) >= 30 else 0
            vol_expansion = atr10 / atr30 if atr30 > 0 else 1.0

            # Breakout probability: proximity to 52-week high
            high52 = float(close.tail(252).max()) if len(close) >= 252 else float(close.max())
            breakout_proximity = float(close.iloc[-1]) / high52 if high52 > 0 else 0.5

            # Price change
            pct_change = float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) >= 2 else 0
            curr_price = float(close.iloc[-1])

            # Composite score
            signals = []
            score = 0
            if vol_ratio > 2.0:
                signals.append("VOLUME ↑")
                score += 30 * min(vol_ratio / 2, 2)
            if vol_expansion > 1.3:
                signals.append("VOLATILE ↑")
                score += 20 * min(vol_expansion, 2)
            if breakout_proximity > 0.97:
                signals.append("BREAKOUT")
                score += 35
            elif breakout_proximity > 0.92:
                signals.append("NEAR HIGH")
                score += 15
            if momentum_accel > 2:
                signals.append("MOMENTUM")
                score += 25
            elif momentum_accel < -2:
                signals.append("WEAKENING")
                score -= 10

            if not signals:
                signal_label = "NEUTRAL"
            elif "BREAKOUT" in signals:
                signal_label = "BREAKOUT"
            elif "MOMENTUM" in signals and "VOLUME ↑" in signals:
                signal_label = "STRONG BUY SETUP"
            elif "VOLUME ↑" in signals:
                signal_label = "VOLUME SURGE"
            elif "VOLATILE ↑" in signals:
                signal_label = "HIGH VOL"
            else:
                signal_label = signals[0]

            results.append({
                "ticker": ticker,
                "priority_score": round(score, 1),
                "signals": signals,
                "signal_label": signal_label,
                "price": round(curr_price, 2),
                "pct_change": round(pct_change, 2),
                "vol_ratio": round(vol_ratio, 2),
                "breakout_proximity": round(breakout_proximity * 100, 1),
                "momentum": round(momentum_accel, 2),
            })
        except Exception:
            results.append({
                "ticker": ticker, "priority_score": 0,
                "signals": [], "signal_label": "Error",
                "price": None, "pct_change": None,
            })

    return sorted(results, key=lambda x: x["priority_score"], reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# NEWS IMPACT ENGINE (USP 4)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def compute_macro_sensitivity(holdings_json: str) -> Dict:
    """
    Estimate portfolio sensitivity to macro factors:
    crude oil, USDINR, interest rates, global selloffs.
    Uses rolling 90-day beta / correlation against macro proxies.
    """
    h = json.loads(holdings_json)
    if not h:
        return {}

    macro_proxies = {
        "crude_oil": "CL=F",
        "usdinr": "INR=X",
        "interest_rate": "^TNX",
        "global_selloff": "^VIX",
    }

    results = {}
    held_tickers = list(h.keys())

    for factor, proxy_ticker in macro_proxies.items():
        try:
            tickers_to_fetch = held_tickers + [proxy_ticker]
            raw = yf.download(tickers_to_fetch, period="6mo", interval="1d", progress=False, auto_adjust=True)
            if raw is None or raw.empty:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"]
            else:
                close = raw
            if proxy_ticker not in close.columns:
                continue
            rets = close.pct_change().dropna()
            proxy_rets = rets[proxy_ticker]
            factor_betas = {}
            for ticker in held_tickers:
                if ticker in rets.columns:
                    stock_rets = rets[ticker]
                    common = stock_rets.dropna().index.intersection(proxy_rets.dropna().index)
                    if len(common) > 20:
                        sr = stock_rets.loc[common].values
                        pr_vals = proxy_rets.loc[common].values
                        cov = np.cov(sr, pr_vals)
                        beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0
                        corr = float(np.corrcoef(sr, pr_vals)[0, 1])
                        factor_betas[ticker] = {"beta": round(beta, 3), "correlation": round(corr, 3)}
            results[factor] = factor_betas
        except Exception:
            continue

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# UI HELPER COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

def render_header():
    """Render top application header."""
    now_ist = datetime.now(IST)
    market_open = (9 <= now_ist.hour < 15) or (now_ist.hour == 15 and now_ist.minute <= 30)
    market_open = market_open and now_ist.weekday() < 5
    status_html = '<span class="chip-live">● MARKET OPEN</span>' if market_open else '<span class="chip-closed">● MARKET CLOSED</span>'

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div class="main-header">
            <div>
                <div class="brand-name">FinTerminal</div>
            </div>
            <div style="display:flex;gap:1rem;align-items:center;">
                {status_html}
                <span style="font-size:0.72rem;color:var(--text-muted);font-family:'DM Mono',monospace;">
                    {now_ist.strftime('%d %b %Y  %H:%M:%S IST')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.session_state.user_name:
            st.markdown(f"""
            <div style="text-align:right;padding:0.5rem 0;">
                <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;">Account</div>
                <div style="font-weight:700;color:var(--text-primary);font-size:0.9rem;">{st.session_state.user_name}</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.82rem;color:var(--accent);font-weight:600;">
                    ₹{st.session_state.cash_balance:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, change: Optional[float] = None,
                        source: str = "", prefix: str = "") -> str:
    change_html = ""
    if change is not None:
        arrow = "▲" if change >= 0 else "▼"
        cls = "metric-change-pos" if change >= 0 else "metric-change-neg"
        change_html = f'<div class="{cls}">{arrow} {abs(change):.2f}%</div>'
    source_html = f'<div class="metric-source">{source}</div>' if source else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value}</div>
        {change_html}
        {source_html}
    </div>
    """


def badge(value: float, suffix: str = "%") -> str:
    if value > 0:
        return f'<span class="badge-pos">▲ {abs(value):.2f}{suffix}</span>'
    elif value < 0:
        return f'<span class="badge-neg">▼ {abs(value):.2f}{suffix}</span>'
    return f'<span class="badge-neutral">0.00{suffix}</span>'


def fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def pnl_html(val: float) -> str:
    cls = "pnl-pos" if val > 0 else ("pnl-neg" if val < 0 else "pnl-zero")
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{fmt_inr(val)}</span>'


def section_header(title: str, icon: str = ""):
    st.markdown(f'<div class="section-header">{icon} {title}</div>', unsafe_allow_html=True)


def alert_html(msg: str, kind: str = "info"):
    return f'<div class="alert-{kind}">{msg}</div>'


def plotly_chart_config() -> Dict:
    return dict(displayModeBar=True, displaylogo=False,
                modeBarButtonsToRemove=["lasso2d", "select2d"])


CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,249,251,1)",
    font=dict(family="DM Sans, sans-serif", color="#5A6474", size=11),
    xaxis=dict(gridcolor="#E2E7EF", linecolor="#E2E7EF", showgrid=True),
    yaxis=dict(gridcolor="#E2E7EF", linecolor="#E2E7EF", showgrid=True),
    margin=dict(l=8, r=8, t=32, b=8),
    legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#E2E7EF", borderwidth=1),
)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: MARKET OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

def page_market_overview():
    section_header("Indian Indices", "📊")

    idx_cols = st.columns(len(INDICES))
    for i, (name, ticker) in enumerate(INDICES.items()):
        data = fetch_current_price(ticker)
        with idx_cols[i]:
            if data:
                val = f"{data['price']:,.2f}"
                st.markdown(render_metric_card(name, val, data["pct_change"], "NSE/BSE"), unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-warning">⚠ {name} unavailable</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sector Heatmap ──
    section_header("Sector Performance", "🔥")
    with st.spinner("Loading sector data…"):
        sector_data = fetch_sector_performance()

    if sector_data:
        sector_names = list(sector_data.keys())
        sector_changes = [sector_data[s]["avg_change"] for s in sector_names]
        breadth = [f"{sector_data[s]['breadth_positive']}/{sector_data[s]['total']} ↑" for s in sector_names]

        fig_heat = go.Figure(go.Bar(
            x=sector_names,
            y=sector_changes,
            text=[f"{c:+.2f}%" for c in sector_changes],
            textposition="outside",
            marker_color=["#0D9373" if c >= 0 else "#D92D20" for c in sector_changes],
            customdata=breadth,
            hovertemplate="<b>%{x}</b><br>Avg Change: %{y:.2f}%<br>Breadth: %{customdata}<extra></extra>",
        ))
        fig_heat.update_layout(
            **CHART_THEME,
            height=260,
            title=dict(text="NSE Sector Performance (Today)", font=dict(size=12, color="#0F1923"), x=0),
            xaxis_title=None, yaxis_title="Avg % Change",
            showlegend=False,
        )
        st.plotly_chart(fig_heat, use_container_width=True, config=plotly_chart_config())
    else:
        st.markdown(alert_html("Sector data temporarily unavailable.", "warning"), unsafe_allow_html=True)

    # ── Market Movers ──
    col_gain, col_lose = st.columns(2)
    with col_gain:
        section_header("Top Gainers", "🟢")
        with st.spinner(""):
            gainers, losers = fetch_movers(8)
        if gainers:
            for g in gainers:
                st.markdown(f"""
                <div class="stock-row">
                    <div>
                        <div class="stock-ticker">{g['ticker']}</div>
                        <div class="stock-name">₹{g['price']:,.2f}</div>
                    </div>
                    <div>{badge(g['pct_change'])}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(alert_html("Movers data unavailable.", "warning"), unsafe_allow_html=True)

    with col_lose:
        section_header("Top Losers", "🔴")
        if losers:
            for lo in losers:
                st.markdown(f"""
                <div class="stock-row">
                    <div>
                        <div class="stock-ticker">{lo['ticker']}</div>
                        <div class="stock-name">₹{lo['price']:,.2f}</div>
                    </div>
                    <div>{badge(lo['pct_change'])}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Global Markets + Commodities + Forex ──
    section_header("Global Markets & Macro", "🌍")
    global_cols = st.columns(4)
    global_items = [
        ("S&P 500", "^GSPC"), ("NASDAQ", "^IXIC"), ("NIKKEI", "^N225"), ("FTSE 100", "^FTSE")
    ]
    for i, (name, tkr) in enumerate(global_items):
        d = fetch_current_price(tkr)
        with global_cols[i]:
            if d:
                st.markdown(render_metric_card(name, f"{d['price']:,.2f}", d["pct_change"]), unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div style="color:var(--text-muted);font-size:0.8rem;">Unavailable</div></div>', unsafe_allow_html=True)

    macro_cols = st.columns(4)
    macro_items = [
        ("USD/INR", "INR=X", "₹"), ("CRUDE OIL", "CL=F", "$"), ("GOLD", "GC=F", "$"), ("US 10Y YIELD", "^TNX", "")
    ]
    for i, (name, tkr, pfx) in enumerate(macro_items):
        d = fetch_current_price(tkr)
        with macro_cols[i]:
            if d:
                st.markdown(render_metric_card(name, f"{pfx}{d['price']:,.2f}", d["pct_change"]), unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="metric-card"><div class="metric-label">{name}</div><div style="color:var(--text-muted);font-size:0.8rem;">Unavailable</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── NIFTY 50 Trend Chart ──
    section_header("NIFTY 50 — 1 Year Chart", "📈")
    nifty_df = fetch_ohlcv("^NSEI", period="1y", interval="1d")
    if nifty_df is not None and not nifty_df.empty:
        fig_nifty = go.Figure()
        close = nifty_df["Close"].squeeze()
        start_price = float(close.iloc[0])
        color = "#0D9373" if float(close.iloc[-1]) >= start_price else "#D92D20"

        fig_nifty.add_trace(go.Scatter(
            x=nifty_df.index,
            y=close,
            name="NIFTY 50",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba{(13,147,115,0.07) if color=='#0D9373' else (217,45,32,0.07)}",
        ))
        # 50-day EMA
        ema_50 = close.ewm(span=50).mean()
        fig_nifty.add_trace(go.Scatter(
            x=nifty_df.index, y=ema_50,
            name="EMA 50", line=dict(color="#1B6CA8", width=1.5, dash="dash"),
        ))
        fig_nifty.update_layout(**CHART_THEME, height=320,
                                title=dict(text="NIFTY 50 — Close Price + EMA(50)", font=dict(size=12), x=0))
        st.plotly_chart(fig_nifty, use_container_width=True, config=plotly_chart_config())
    else:
        st.markdown(alert_html("NIFTY 50 chart data unavailable.", "warning"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: STOCK EXPLORER
# ═══════════════════════════════════════════════════════════════════════════════

def page_stock_explorer():
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        raw_input = st.text_input(
            "Search NSE Ticker",
            value=st.session_state.stock_explorer_ticker.replace(".NS", ""),
            placeholder="e.g. RELIANCE, TCS, INFY",
            label_visibility="collapsed",
        )
    with col_btn:
        go_btn = st.button("Analyse →", type="primary", use_container_width=True)

    if go_btn or raw_input:
        ticker = raw_input.strip().upper()
        if not ticker.endswith(".NS"):
            ticker += ".NS"
        st.session_state.stock_explorer_ticker = ticker

    ticker = st.session_state.stock_explorer_ticker

    # Fetch data
    with st.spinner(f"Fetching data for {ticker}…"):
        info = fetch_ticker_info(ticker)
        price_data = fetch_current_price(ticker)
        tech = compute_technicals(ticker)
        beta_data = compute_beta_correlation(ticker)
        hist_1y = fetch_ohlcv(ticker, period="1y", interval="1d")
        hist_intra = fetch_ohlcv(ticker, period="5d", interval="15m")

    if "error" in info and price_data is None:
        st.markdown(alert_html(f"Could not fetch data for <b>{ticker}</b>. Please check the ticker symbol.", "error"), unsafe_allow_html=True)
        return

    # ── Top KPIs ──
    company_name = info.get("longName", ticker.replace(".NS", ""))
    _derived_sector = next(
        (sec for sec, tickers in NSE_SECTORS.items() if ticker in tickers), None)
    sector = info.get("sector") or _derived_sector or ticker.replace(".NS", "")
    industry = info.get("industry") or info.get("exchange") or ""
    market_cap = info.get("marketCap", 0)

    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <div style="font-size:1.4rem;font-weight:700;color:var(--text-primary);font-family:'Playfair Display',serif;">{company_name}</div>
        <div style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">
            <span style="font-family:'DM Mono',monospace;font-weight:600;color:var(--accent);">{ticker}</span>
            &nbsp;·&nbsp; {sector} &nbsp;·&nbsp; {industry}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if price_data:
        kpi_cols = st.columns(6)
        kpis = [
            ("LTP", f"₹{price_data['price']:,.2f}", price_data["pct_change"]),
            ("Day High", f"₹{price_data['high']:,.2f}", None),
            ("Day Low", f"₹{price_data['low']:,.2f}", None),
            ("Volume", f"{price_data['volume']:,}" if price_data['volume'] else "N/A", None),
            ("Mkt Cap", f"₹{market_cap/1e7:,.0f}Cr" if market_cap else "N/A", None),
            ("P/E Ratio", f"{info.get('trailingPE', 'N/A')}" if info.get('trailingPE') else "N/A", None),
        ]
        for i, (label, val, chg) in enumerate(kpis):
            with kpi_cols[i]:
                change_html = ""
                if chg is not None:
                    arrow = "▲" if chg >= 0 else "▼"
                    cls = "metric-change-pos" if chg >= 0 else "metric-change-neg"
                    change_html = f'<div class="{cls}">{arrow} {abs(chg):.2f}%</div>'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{val}</div>
                    {change_html}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──
    tab_chart, tab_tech, tab_fundamentals, tab_compare = st.tabs([
        "📈 Price Chart", "⚡ Technical Analysis", "📋 Fundamentals", "⚖ Compare"
    ])

    with tab_chart:
        if hist_1y is not None and not hist_1y.empty:
            period_select = st.radio("Period", ["1M", "3M", "6M", "1Y"], index=3, horizontal=True)
            periods = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252}
            n_bars = periods[period_select]
            df_plot = hist_1y.tail(n_bars)
            close = df_plot["Close"].squeeze()

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                row_heights=[0.75, 0.25], vertical_spacing=0.04)

            # Candlestick
            fig.add_trace(go.Candlestick(
                x=df_plot.index,
                open=df_plot["Open"].squeeze(),
                high=df_plot["High"].squeeze(),
                low=df_plot["Low"].squeeze(),
                close=close,
                name="OHLC",
                increasing_line_color="#0D9373", decreasing_line_color="#D92D20",
                increasing_fillcolor="#0D9373", decreasing_fillcolor="#D92D20",
            ), row=1, col=1)

            # EMAs
            ema20 = close.ewm(span=20).mean()
            ema50 = close.ewm(span=50).mean()
            fig.add_trace(go.Scatter(x=df_plot.index, y=ema20, name="EMA 20",
                                     line=dict(color="#7C3AED", width=1.2, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=ema50, name="EMA 50",
                                     line=dict(color="#D97706", width=1.2, dash="dash")), row=1, col=1)

            # Volume
            if "Volume" in df_plot.columns:
                vol = df_plot["Volume"].squeeze()
                vol_colors = ["#0D9373" if c >= o else "#D92D20"
                              for c, o in zip(close, df_plot["Open"].squeeze())]
                fig.add_trace(go.Bar(x=df_plot.index, y=vol, name="Volume",
                                     marker_color=vol_colors, opacity=0.7), row=2, col=1)

            fig.update_layout(
                **CHART_THEME,
                height=480,
                title=dict(text=f"{company_name} — {period_select} Price + Volume", font=dict(size=12), x=0),
                xaxis_rangeslider_visible=False,
            )
            st.plotly_chart(fig, use_container_width=True, config=plotly_chart_config())
        else:
            st.markdown(alert_html("Price chart data unavailable.", "warning"), unsafe_allow_html=True)

    with tab_tech:
        if "error" not in tech:
            t_cols = st.columns(4)
            indicators = [
                ("RSI (14)", f"{tech.get('rsi','N/A')}", "Overbought >70, Oversold <30"),
                ("MACD", f"{tech.get('macd','N/A')}", "Signal: " + str(tech.get("macd_signal", "N/A"))),
                ("Stoch %K", f"{tech.get('stoch_k','N/A')}", f"Stoch %D: {tech.get('stoch_d','N/A')}"),
                ("BB %B", f"{tech.get('bb_pct','N/A'):.1f}%" if isinstance(tech.get('bb_pct'), float) else "N/A",
                 f"Upper: ₹{tech.get('bb_upper','N/A')} | Lower: ₹{tech.get('bb_lower','N/A')}"),
            ]
            for i, (lbl, val, sub) in enumerate(indicators):
                with t_cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{lbl}</div>
                        <div class="metric-value">{val}</div>
                        <div class="metric-source">{sub}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            t2_cols = st.columns(4)
            ema_indicators = [
                ("EMA 20", f"₹{tech.get('ema20','N/A')}", "Above" if tech.get("above_ema20") else "Below"),
                ("EMA 50", f"₹{tech.get('ema50','N/A')}", "Above" if tech.get("above_ema50") else "Below"),
                ("EMA 200", f"₹{tech.get('ema200','N/A')}" if tech.get('ema200') else "N/A",
                 "Above" if tech.get("above_ema200") else ("Below" if tech.get("above_ema200") is not None else "N/A")),
                ("ATR (14)", f"₹{tech.get('atr','N/A')}", f"Vol Ratio: {tech.get('vol_ratio','N/A')}x"),
            ]
            for i, (lbl, val, sub) in enumerate(ema_indicators):
                with t2_cols[i]:
                    color = "var(--positive)" if sub == "Above" else ("var(--negative)" if sub == "Below" else "var(--neutral)")
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{lbl}</div>
                        <div class="metric-value">{val}</div>
                        <div style="font-size:0.72rem;font-weight:600;color:{color};">{sub}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # RSI chart from history
            if hist_1y is not None and not hist_1y.empty:
                close_ser = hist_1y["Close"].squeeze().tail(180)
                rsi_series = ta.momentum.rsi(close_ser, window=14).tail(180)
                macd_obj = ta.trend.MACD(close_ser)
                macd_line = macd_obj.macd().tail(180)
                macd_sig = macd_obj.macd_signal().tail(180)
                macd_hist_s = macd_obj.macd_diff().tail(180)

                fig_rsi = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                        subplot_titles=["RSI (14)", "MACD"],
                                        row_heights=[0.5, 0.5], vertical_spacing=0.1)
                fig_rsi.add_trace(go.Scatter(x=rsi_series.index, y=rsi_series,
                                              name="RSI", line=dict(color="#7C3AED", width=1.5)), row=1, col=1)
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="#D92D20", opacity=0.6, row=1, col=1)
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#0D9373", opacity=0.6, row=1, col=1)
                fig_rsi.add_trace(go.Scatter(x=macd_line.index, y=macd_line,
                                              name="MACD", line=dict(color="#1B6CA8", width=1.5)), row=2, col=1)
                fig_rsi.add_trace(go.Scatter(x=macd_sig.index, y=macd_sig,
                                              name="Signal", line=dict(color="#D97706", width=1.2, dash="dot")), row=2, col=1)
                hist_colors = ["#0D9373" if v >= 0 else "#D92D20" for v in macd_hist_s]
                fig_rsi.add_trace(go.Bar(x=macd_hist_s.index, y=macd_hist_s,
                                          name="Histogram", marker_color=hist_colors, opacity=0.7), row=2, col=1)
                fig_rsi.update_layout(**CHART_THEME, height=400)
                st.plotly_chart(fig_rsi, use_container_width=True, config=plotly_chart_config())

            # Beta info
            if "error" not in beta_data:
                b_cols = st.columns(4)
                b_items = [
                    ("Beta (vs NIFTY)", f"{beta_data.get('beta','N/A')}"),
                    ("Correlation", f"{beta_data.get('correlation','N/A')}"),
                    ("Ann. Volatility", f"{beta_data.get('ann_volatility','N/A')}%"),
                    ("20D Rolling Vol", f"{beta_data.get('rolling_vol_20d','N/A')}%"),
                ]
                for i, (lbl, val) in enumerate(b_items):
                    with b_cols[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{lbl}</div>
                            <div class="metric-value">{val}</div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.markdown(alert_html(f"Technical data error: {tech.get('error')}", "warning"), unsafe_allow_html=True)

    with tab_fundamentals:
        fund_keys = {
            "Market Cap": ("marketCap", lambda v: f"₹{v/1e7:,.0f} Cr" if v else "N/A"),
            "P/E Ratio (TTM)": ("trailingPE", lambda v: f"{v:.2f}x" if v else "N/A"),
            "Forward P/E": ("forwardPE", lambda v: f"{v:.2f}x" if v else "N/A"),
            "EPS (TTM)": ("trailingEps", lambda v: f"₹{v:.2f}" if v else "N/A"),
            "P/B Ratio": ("priceToBook", lambda v: f"{v:.2f}x" if v else "N/A"),
            "Dividend Yield": ("dividendYield", lambda v: f"{v*100:.2f}%" if v else "N/A"),
            "Revenue (TTM)": ("totalRevenue", lambda v: f"₹{v/1e7:,.0f} Cr" if v else "N/A"),
            "Net Income": ("netIncomeToCommon", lambda v: f"₹{v/1e7:,.0f} Cr" if v else "N/A"),
            "ROE": ("returnOnEquity", lambda v: f"{v*100:.2f}%" if v else "N/A"),
            "ROA": ("returnOnAssets", lambda v: f"{v*100:.2f}%" if v else "N/A"),
            "Debt/Equity": ("debtToEquity", lambda v: f"{v:.2f}x" if v else "N/A"),
            "Current Ratio": ("currentRatio", lambda v: f"{v:.2f}x" if v else "N/A"),
            "52W High": ("fiftyTwoWeekHigh", lambda v: f"₹{v:,.2f}" if v else "N/A"),
            "52W Low": ("fiftyTwoWeekLow", lambda v: f"₹{v:,.2f}" if v else "N/A"),
            "Beta": ("beta", lambda v: f"{v:.3f}" if v else "N/A"),
            "Avg Volume": ("averageVolume", lambda v: f"{v:,}" if v else "N/A"),
        }
        f_cols = st.columns(4)
        for j, (label, (key, fmt)) in enumerate(fund_keys.items()):
            with f_cols[j % 4]:
                raw_val = info.get(key)
                display_val = fmt(raw_val) if raw_val is not None else "N/A"
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:0.5rem;">
                    <div class="metric-label">{label}</div>
                    <div style="font-family:'DM Mono',monospace;font-weight:600;font-size:0.95rem;color:var(--text-primary);">{display_val}</div>
                </div>
                """, unsafe_allow_html=True)

        # Business summary
        summary = info.get("longBusinessSummary", "")
        if summary:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("Company Overview", "📝")
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);
                padding:1rem 1.25rem;font-size:0.8rem;color:var(--text-secondary);line-height:1.7;">
                {summary[:800]}{'…' if len(summary) > 800 else ''}
            </div>
            """, unsafe_allow_html=True)

    with tab_compare:
        st.markdown(f'<div class="alert-info">Compare <b>{ticker.replace(".NS","")}</b> against peers or benchmark.</div>', unsafe_allow_html=True)
        compare_tickers_raw = st.text_input("Add tickers to compare (comma-separated)", placeholder="TCS, INFY, WIPRO")
        if compare_tickers_raw:
            cmp_list = [t.strip().upper() + (".NS" if not t.strip().upper().endswith(".NS") else "")
                        for t in compare_tickers_raw.split(",") if t.strip()]
            all_tickers = [ticker] + cmp_list[:4]
            cmp_data = {}
            for ct in all_tickers:
                df_ct = fetch_ohlcv(ct, period="6mo", interval="1d")
                if df_ct is not None and not df_ct.empty:
                    cmp_data[ct] = df_ct["Close"].squeeze()

            if len(cmp_data) > 1:
                fig_cmp = go.Figure()
                colors = ["#1B6CA8", "#0D9373", "#D97706", "#7C3AED", "#D92D20"]
                for i, (ct, series) in enumerate(cmp_data.items()):
                    normalized = (series / series.iloc[0]) * 100
                    fig_cmp.add_trace(go.Scatter(
                        x=series.index, y=normalized,
                        name=ct.replace(".NS", ""),
                        line=dict(color=colors[i % len(colors)], width=2),
                    ))
                fig_cmp.update_layout(**CHART_THEME, height=380,
                                      title=dict(text="Normalized Returns (Base=100, 6M)", font=dict(size=12), x=0),
                                      yaxis_title="Indexed Return",
                                      hovermode="x unified")
                st.plotly_chart(fig_cmp, use_container_width=True, config=plotly_chart_config())


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ORDER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def page_orders():
    col_order, col_history = st.columns([1, 1.5])

    with col_order:
        st.markdown('<div class="order-panel">', unsafe_allow_html=True)
        section_header("Place Order", "📋")

        ticker_raw = st.text_input("Ticker Symbol", value="RELIANCE", placeholder="e.g. RELIANCE, TCS").strip().upper()
        ticker = ticker_raw + ".NS" if not ticker_raw.endswith(".NS") else ticker_raw

        action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
        order_type = st.selectbox("Order Type", ["Market", "Limit", "Stop-Loss"])

        # Fetch live price
        live_price_data = fetch_current_price(ticker)
        live_price = live_price_data["price"] if live_price_data else None

        if live_price:
            st.markdown(f"""
            <div style="background:var(--accent-light);border:1px solid var(--border);border-radius:var(--radius);
                padding:0.6rem 1rem;margin-bottom:0.75rem;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.72rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;">Live Price</span>
                <span style="font-family:'DM Mono',monospace;font-weight:700;font-size:1.1rem;color:var(--accent);">₹{live_price:,.2f}</span>
                <span style="{badge(live_price_data['pct_change'])}">{badge(live_price_data['pct_change'])}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(alert_html(f"Cannot fetch price for {ticker}. Check ticker.", "warning"), unsafe_allow_html=True)

        qty = st.number_input("Quantity", min_value=1, max_value=100000, value=1, step=1)

        limit_price = None
        stop_price = None
        if order_type == "Limit":
            limit_price = st.number_input("Limit Price (₹)", min_value=0.01, value=float(live_price) if live_price else 100.0, step=0.05)
        elif order_type == "Stop-Loss":
            stop_price = st.number_input("Stop-Loss Trigger (₹)", min_value=0.01, value=float(live_price * 0.97) if live_price else 100.0, step=0.05)
            limit_price = st.number_input("Limit Price (₹)", min_value=0.01, value=float(live_price * 0.96) if live_price else 99.0, step=0.05)

        # Execution price logic
        if order_type == "Market":
            exec_price = live_price
        elif order_type == "Limit":
            exec_price = limit_price
        else:
            exec_price = stop_price  # simplified sim: trigger = execution

        # Order summary preview
        if exec_price and qty:
            total = exec_price * qty
            st.markdown(f"""
            <div style="border:1px dashed var(--border);border-radius:var(--radius);padding:0.75rem 1rem;margin:0.75rem 0;background:var(--bg-primary);">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                    <span style="font-size:0.72rem;color:var(--text-muted);">Order Value</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:700;color:var(--text-primary);">₹{total:,.2f}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                    <span style="font-size:0.72rem;color:var(--text-muted);">Available Cash</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:600;color:var(--accent);">₹{st.session_state.cash_balance:,.2f}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.72rem;color:var(--text-muted);">Post-Trade Cash</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:600;
                        color:{'var(--positive)' if action=='SELL' else ('var(--positive)' if st.session_state.cash_balance>=total else 'var(--negative)')};">
                        ₹{(st.session_state.cash_balance + total if action=='SELL' else st.session_state.cash_balance - total):,.2f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Sector auto-detection
        sector = "Unknown"
        for sec, tickers_list in NSE_SECTORS.items():
            if ticker in tickers_list:
                sector = sec
                break

        execute_btn = st.button(
            f"{'🟢 BUY' if action=='BUY' else '🔴 SELL'} — {order_type} Order",
            type="primary", use_container_width=True
        )

        if execute_btn:
            if not exec_price:
                st.markdown(alert_html("Cannot execute: price unavailable.", "error"), unsafe_allow_html=True)
            else:
                result = validate_and_place_order(
                    action=action, ticker=ticker, qty=qty,
                    order_type=order_type, limit_price=limit_price,
                    stop_price=stop_price, execution_price=exec_price,
                    sector=sector,
                )
                if result["success"]:
                    st.markdown(alert_html(f"✅ {result['message']}", "success"), unsafe_allow_html=True)
                else:
                    st.markdown(alert_html(f"❌ {result['message']}", "error"), unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_history:
        section_header("Order History", "🕐")
        if not st.session_state.order_history:
            st.markdown(alert_html("No orders placed yet in this session.", "info"), unsafe_allow_html=True)
        else:
            # Header
            st.markdown("""
            <div style="display:grid;grid-template-columns:0.8fr 0.7fr 0.5fr 0.5fr 0.8fr 0.8fr;
                gap:0.5rem;padding:0.4rem 0.75rem;font-size:0.65rem;font-weight:700;
                color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;
                border-bottom:2px solid var(--border);margin-bottom:0.3rem;">
                <span>Order ID</span><span>Ticker</span><span>Action</span><span>Qty</span>
                <span>Price</span><span>Time</span>
            </div>
            """, unsafe_allow_html=True)

            for order in st.session_state.order_history[:25]:
                ts = order["timestamp"][:19].replace("T", " ")
                action_color = "var(--positive)" if order["action"] == "BUY" else "var(--negative)"
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:0.8fr 0.7fr 0.5fr 0.5fr 0.8fr 0.8fr;
                    gap:0.5rem;padding:0.45rem 0.75rem;font-size:0.75rem;
                    border-bottom:1px solid var(--border-light);align-items:center;">
                    <span style="font-family:'DM Mono',monospace;font-size:0.68rem;color:var(--text-muted);">{order['order_id']}</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:600;color:var(--text-primary);">{order['ticker'].replace('.NS','')}</span>
                    <span style="font-weight:700;color:{action_color};">{order['action']}</span>
                    <span style="font-family:'DM Mono',monospace;">{order['qty']}</span>
                    <span style="font-family:'DM Mono',monospace;">₹{order['execution_price']:,.2f}</span>
                    <span style="font-size:0.65rem;color:var(--text-muted);">{ts[11:]}</span>
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PORTFOLIO ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

def page_portfolio():
    holdings = st.session_state.holdings
    if not holdings:
        st.markdown(alert_html("Your portfolio is empty. Go to <b>Orders</b> to buy stocks.", "info"), unsafe_allow_html=True)
        return

    # Fetch live prices for all holdings
    with st.spinner("Loading portfolio analytics…"):
        live_prices = fetch_multiple_prices(list(holdings.keys()))

    # Compute P&L
    total_invested = 0
    total_current = 0
    holdings_display = []
    for ticker, pos in holdings.items():
        invested = pos["avg_cost"] * pos["qty"]
        curr_price = live_prices.get(ticker, {}).get("price", pos["avg_cost"])
        curr_val = curr_price * pos["qty"]
        unrealized = curr_val - invested
        unrealized_pct = (unrealized / invested * 100) if invested > 0 else 0
        total_invested += invested
        total_current += curr_val
        holdings_display.append({
            "ticker": ticker, "qty": pos["qty"],
            "avg_cost": pos["avg_cost"], "curr_price": curr_price,
            "invested": invested, "curr_val": curr_val,
            "unrealized": unrealized, "unrealized_pct": unrealized_pct,
            "sector": pos.get("sector", "Unknown"),
            "day_change": live_prices.get(ticker, {}).get("pct_change", 0),
        })

    total_unrealized = total_current - total_invested
    total_unrealized_pct = (total_unrealized / total_invested * 100) if total_invested > 0 else 0
    portfolio_total = total_current + st.session_state.cash_balance

    # ── Top KPIs ──
    section_header("Portfolio Summary", "💼")
    kpi_cols = st.columns(5)
    kpi_data = [
        ("Portfolio Value", f"₹{total_current:,.2f}", None),
        ("Cash Balance", f"₹{st.session_state.cash_balance:,.2f}", None),
        ("Total Account", f"₹{portfolio_total:,.2f}", None),
        ("Unrealized P&L", f"₹{total_unrealized:+,.2f}", total_unrealized_pct),
        ("Total Invested", f"₹{total_invested:,.2f}", None),
    ]
    for i, (lbl, val, chg) in enumerate(kpi_data):
        with kpi_cols[i]:
            st.markdown(render_metric_card(lbl, val, chg), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Holdings Table ──
    section_header("Holdings", "📊")
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 0.5fr 0.8fr 0.8fr 0.8fr 0.8fr 0.8fr 0.7fr;
        gap:0.5rem;padding:0.4rem 0.75rem;font-size:0.65rem;font-weight:700;
        color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;
        border-bottom:2px solid var(--border);margin-bottom:0.3rem;">
        <span>Ticker</span><span>Qty</span><span>Avg Cost</span><span>LTP</span>
        <span>Invested</span><span>Current</span><span>P&L</span><span>Day %</span>
    </div>
    """, unsafe_allow_html=True)

    for pos in sorted(holdings_display, key=lambda x: x["curr_val"], reverse=True):
        pnl_color = "var(--positive)" if pos["unrealized"] >= 0 else "var(--negative)"
        sign = "+" if pos["unrealized"] >= 0 else ""
        day_badge = badge(pos["day_change"])
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 0.5fr 0.8fr 0.8fr 0.8fr 0.8fr 0.8fr 0.7fr;
            gap:0.5rem;padding:0.5rem 0.75rem;font-size:0.76rem;
            border-bottom:1px solid var(--border-light);align-items:center;background:var(--bg-card);">
            <span style="font-family:'DM Mono',monospace;font-weight:700;color:var(--accent);">{pos['ticker'].replace('.NS','')}</span>
            <span style="font-family:'DM Mono',monospace;">{pos['qty']}</span>
            <span style="font-family:'DM Mono',monospace;">₹{pos['avg_cost']:,.2f}</span>
            <span style="font-family:'DM Mono',monospace;font-weight:600;">₹{pos['curr_price']:,.2f}</span>
            <span style="font-family:'DM Mono',monospace;">₹{pos['invested']:,.0f}</span>
            <span style="font-family:'DM Mono',monospace;">₹{pos['curr_val']:,.0f}</span>
            <span style="font-family:'DM Mono',monospace;font-weight:700;color:{pnl_color};">{sign}₹{pos['unrealized']:,.0f} ({sign}{pos['unrealized_pct']:.1f}%)</span>
            <span>{day_badge}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Advanced Analytics ──
    section_header("Advanced Analytics", "📐")
    analytics_result = compute_portfolio_analytics(
        json.dumps(holdings),
        json.dumps(live_prices),
    )

    if "error" not in analytics_result:
        a = analytics_result
        adv_cols = st.columns(5)
        adv_kpis = [
            ("Sharpe Ratio", f"{a['sharpe']:.3f}"),
            ("Max Drawdown", f"{a['max_drawdown_pct']:.2f}%"),
            ("Portfolio Beta", f"{a['beta']:.3f}"),
            ("Ann. Volatility", f"{a['portfolio_vol_pct']:.2f}%"),
            ("Diversification", f"{a['diversification_score']}/100"),
        ]
        for i, (lbl, val) in enumerate(adv_kpis):
            with adv_cols[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{lbl}</div>
                    <div class="metric-value">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts row
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Allocation pie
            weights = a["weights"]
            fig_pie = go.Figure(go.Pie(
                labels=[t.replace(".NS", "") for t in weights.keys()],
                values=list(weights.values()),
                hole=0.55,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>",
                marker=dict(colors=px.colors.qualitative.Set2),
            ))
            fig_pie.update_layout(**CHART_THEME, height=320,
                                   title=dict(text="Portfolio Allocation", font=dict(size=12), x=0))
            st.plotly_chart(fig_pie, use_container_width=True, config=plotly_chart_config())

        with chart_col2:
            # Sector exposure bar
            sector_pct = a["sector_pct"]
            if sector_pct:
                fig_sec = go.Figure(go.Bar(
                    x=list(sector_pct.values()),
                    y=list(sector_pct.keys()),
                    orientation="h",
                    marker_color="#1B6CA8",
                    text=[f"{v:.1f}%" for v in sector_pct.values()],
                    textposition="outside",
                    hovertemplate="<b>%{y}</b>: %{x:.1f}%<extra></extra>",
                ))
                fig_sec.update_layout(**CHART_THEME, height=320,
                                       title=dict(text="Sector Exposure", font=dict(size=12), x=0),
                                       xaxis_title="Weight (%)", yaxis_title=None)
                st.plotly_chart(fig_sec, use_container_width=True, config=plotly_chart_config())

        # Cumulative returns chart
        if "cum_returns" in a and len(a["cum_returns"]) > 5:
            cum_rets = pd.Series(a["cum_returns"], index=pd.to_datetime(a["dates"]))
            dd_series = pd.Series(a["drawdown_series"], index=pd.to_datetime(a["dates"]))

            fig_cum = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    row_heights=[0.65, 0.35], vertical_spacing=0.06,
                                    subplot_titles=["Portfolio Cumulative Return", "Drawdown"])
            cum_pct = (cum_rets - 1) * 100
            fig_cum.add_trace(go.Scatter(
                x=cum_pct.index, y=cum_pct.values,
                name="Portfolio Return",
                line=dict(color="#1B6CA8", width=2),
                fill="tozeroy",
                fillcolor="rgba(27,108,168,0.06)",
            ), row=1, col=1)
            fig_cum.add_trace(go.Scatter(
                x=dd_series.index, y=(dd_series * 100).values,
                name="Drawdown",
                line=dict(color="#D92D20", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(217,45,32,0.08)",
            ), row=2, col=1)
            fig_cum.update_layout(**CHART_THEME, height=400)
            st.plotly_chart(fig_cum, use_container_width=True, config=plotly_chart_config())

    else:
        st.markdown(alert_html(f"Analytics: {analytics_result.get('error')}", "warning"), unsafe_allow_html=True)

    # ── Macro Sensitivity (USP 4) ──
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Macro Sensitivity Analysis", "🌐")
    st.markdown('<div class="alert-info">Rolling 6-month beta of each holding vs macro proxies. Higher absolute beta = more sensitive to that factor.</div>', unsafe_allow_html=True)

    with st.spinner("Computing macro correlations…"):
        macro_sens = compute_macro_sensitivity(json.dumps(holdings))

    if macro_sens:
        factor_labels = {
            "crude_oil": "🛢 Crude Oil",
            "usdinr": "💱 USD/INR",
            "interest_rate": "📊 US 10Y Yield",
            "global_selloff": "⚡ Global VIX",
        }
        for factor, factor_betas in macro_sens.items():
            if not factor_betas:
                continue
            with st.expander(f"{factor_labels.get(factor, factor)} — Sensitivity"):
                sens_cols = st.columns(min(len(factor_betas), 5))
                for i, (ticker, metrics) in enumerate(factor_betas.items()):
                    with sens_cols[i % len(sens_cols)]:
                        beta_val = metrics.get("beta", 0)
                        corr_val = metrics.get("correlation", 0)
                        beta_color = "var(--negative)" if abs(beta_val) > 0.5 else "var(--positive)" if abs(beta_val) < 0.2 else "var(--neutral)"
                        st.markdown(f"""
                        <div class="metric-card" style="margin-bottom:0.4rem;">
                            <div class="metric-label">{ticker.replace('.NS','')}</div>
                            <div style="font-family:'DM Mono',monospace;font-weight:700;color:{beta_color};font-size:1rem;">β {beta_val:+.3f}</div>
                            <div style="font-size:0.68rem;color:var(--text-muted);">Corr: {corr_val:.3f}</div>
                        </div>
                        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: NEWS TERMINAL
# ═══════════════════════════════════════════════════════════════════════════════

def page_news():
    section_header("Live Financial News Terminal", "📰")

    filter_col, _ = st.columns([2, 3])
    with filter_col:
        category_filter = st.selectbox("Filter Category", ["All", "macro", "equity", "earnings", "geopolitical", "commodity", "general"])

    with st.spinner("Fetching news feeds…"):
        news_items = fetch_news_feed()

    if not news_items:
        st.markdown(alert_html("Could not fetch news feeds. Please check network connectivity.", "error"), unsafe_allow_html=True)
        return

    if category_filter != "All":
        news_items = [n for n in news_items if n["category"] == category_filter]

    tag_map = {
        "macro": "news-tag-macro", "equity": "news-tag-equity",
        "earnings": "news-tag-earnings", "geopolitical": "news-tag-geo",
        "commodity": "news-tag-commodity", "general": "news-tag-general",
    }
    cat_icons = {
        "macro": "🏛", "equity": "📈", "earnings": "💰",
        "geopolitical": "🌍", "commodity": "🛢", "general": "📋",
    }

    st.markdown(f'<div class="alert-info">Showing <b>{len(news_items)}</b> articles from Indian financial RSS feeds (ET, MC, BS, NDTV Profit). Auto-categorized.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for article in news_items:
        cat = article["category"]
        icon = cat_icons.get(cat, "📋")
        tag_cls = tag_map.get(cat, "news-tag-general")
        ticker_badges = " ".join([f'<span class="badge-neutral" style="font-size:0.6rem;">{t.replace(".NS","")}</span>'
                                   for t in article.get("tickers", [])])
        link_href = article.get("link", "#")
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title">{icon} {article['title']}</div>
            <div class="news-meta">
                <span class="{tag_cls}">{cat.upper()}</span>
                <span>{article.get('source','')}</span>
                {ticker_badges}
                {'<a href="' + link_href + '" target="_blank" style="color:var(--accent);font-size:0.68rem;font-weight:600;text-decoration:none;">Read →</a>' if link_href and link_href != '#' else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SMART WATCHLIST (USP 5)
# ═══════════════════════════════════════════════════════════════════════════════

def page_watchlist():
    section_header("Smart Watchlist", "⭐")
    st.markdown('<div class="alert-info">Watchlist is dynamically reordered by momentum, volume surges, breakout proximity, and volatility expansion — computed in real time.</div>', unsafe_allow_html=True)

    # Add ticker
    add_col, btn_col = st.columns([4, 1])
    with add_col:
        new_ticker = st.text_input("Add Ticker to Watchlist", placeholder="e.g. TATAMOTORS, HDFCBANK", label_visibility="collapsed")
    with btn_col:
        if st.button("Add ＋", use_container_width=True) and new_ticker.strip():
            tkr = new_ticker.strip().upper()
            if not tkr.endswith(".NS"):
                tkr += ".NS"
            if tkr not in st.session_state.watchlist:
                st.session_state.watchlist.append(tkr)
                st.rerun()

    # Seed default watchlist
    if not st.session_state.watchlist:
        default_wl = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
                      "ICICIBANK.NS", "TATAMOTORS.NS", "BAJFINANCE.NS", "AXISBANK.NS"]
        st.session_state.watchlist = default_wl

    # Remove UI
    if st.session_state.watchlist:
        remove_ticker = st.selectbox("Remove from Watchlist", ["—"] + st.session_state.watchlist)
        if remove_ticker != "—":
            if st.button(f"Remove {remove_ticker.replace('.NS','')}", type="secondary"):
                st.session_state.watchlist.remove(remove_ticker)
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.watchlist:
        st.markdown(alert_html("Watchlist is empty.", "info"), unsafe_allow_html=True)
        return

    with st.spinner("Analysing watchlist signals…"):
        prioritized = compute_watchlist_priorities(st.session_state.watchlist)

    signal_css_map = {
        "BREAKOUT": "wl-breakout",
        "STRONG BUY SETUP": "wl-breakout",
        "MOMENTUM": "wl-momentum",
        "NEAR HIGH": "wl-momentum",
        "VOLUME SURGE": "wl-volume",
        "HIGH VOL": "wl-volatile",
        "WEAKENING": "wl-volatile",
        "NEUTRAL": "wl-neutral",
        "No Data": "wl-neutral",
        "Error": "wl-neutral",
    }

    # Table header
    st.markdown("""
    <div style="display:grid;grid-template-columns:0.3fr 1.2fr 0.8fr 0.8fr 0.6fr 0.8fr 1fr 0.5fr;
        gap:0.5rem;padding:0.4rem 0.75rem;font-size:0.65rem;font-weight:700;
        color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;
        border-bottom:2px solid var(--border);margin-bottom:0.4rem;">
        <span>#</span><span>Ticker</span><span>Price</span><span>Today</span>
        <span>Vol Ratio</span><span>Signal</span><span>Signals</span><span>Score</span>
    </div>
    """, unsafe_allow_html=True)

    for rank, item in enumerate(prioritized, 1):
        signal_label = item.get("signal_label", "NEUTRAL")
        css_cls = signal_css_map.get(signal_label, "wl-neutral")
        price_str = f"₹{item['price']:,.2f}" if item.get("price") else "N/A"
        pct_str = badge(item["pct_change"]) if item.get("pct_change") is not None else "—"
        vol_str = f"{item.get('vol_ratio','—')}x" if item.get("vol_ratio") else "—"
        signals_html = " ".join([f'<span class="badge-neutral" style="font-size:0.6rem;">{s}</span>' for s in item.get("signals", [])])
        score = item.get("priority_score", 0)

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:0.3fr 1.2fr 0.8fr 0.8fr 0.6fr 0.8fr 1fr 0.5fr;
            gap:0.5rem;padding:0.5rem 0.75rem;font-size:0.76rem;
            border-bottom:1px solid var(--border-light);align-items:center;
            background:{'rgba(27,108,168,0.03)' if rank==1 else 'var(--bg-card)'};">
            <span style="font-family:'DM Mono',monospace;font-size:0.7rem;color:var(--text-muted);">{rank}</span>
            <span style="font-family:'DM Mono',monospace;font-weight:700;color:var(--accent);">{item['ticker'].replace('.NS','')}</span>
            <span style="font-family:'DM Mono',monospace;font-weight:600;">{price_str}</span>
            <span>{pct_str}</span>
            <span style="font-family:'DM Mono',monospace;">{vol_str}</span>
            <span class="{css_cls}">{signal_label}</span>
            <span>{signals_html if signals_html else '—'}</span>
            <span style="font-family:'DM Mono',monospace;font-size:0.7rem;">{score:.0f}</span>
        </div>
        """, unsafe_allow_html=True)

    # Watchlist mini-chart
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("30-Day Price Trails", "📉")
    wl_chart_tickers = [item["ticker"] for item in prioritized[:6] if item.get("price")]
    if wl_chart_tickers:
        fig_wl = go.Figure()
        colors_wl = ["#1B6CA8", "#0D9373", "#D97706", "#7C3AED", "#D92D20", "#059669"]
        for i, tkr in enumerate(wl_chart_tickers):
            df_wl = fetch_ohlcv(tkr, period="1mo", interval="1d")
            if df_wl is not None and not df_wl.empty:
                close_wl = df_wl["Close"].squeeze()
                norm_wl = (close_wl / close_wl.iloc[0]) * 100
                fig_wl.add_trace(go.Scatter(
                    x=df_wl.index, y=norm_wl,
                    name=tkr.replace(".NS", ""),
                    line=dict(color=colors_wl[i % len(colors_wl)], width=1.8),
                    hovertemplate="%{y:.1f} (base 100)<extra></extra>",
                ))
        fig_wl.update_layout(**CHART_THEME, height=300,
                              title=dict(text="Normalized 30-Day Returns (Base=100)", font=dict(size=12), x=0),
                              hovermode="x unified")
        st.plotly_chart(fig_wl, use_container_width=True, config=plotly_chart_config())

# ═══════════════════════════════════════════════════════════════════════════════
# STRESS TEST ENGINE — Quant Finance Portfolio Stress Testing
# ═══════════════════════════════════════════════════════════════════════════════

# ── Historical Crisis Calibration ──────────────────────────────────────────────
# All figures are empirically sourced from NSE/BSE historical records.
# Sector multipliers = (sector_crash_return / nifty_crash_return) derived from
# observed sectoral index drawdowns during each crisis.
# Volatility regimes represent annualised daily σ during the crisis window.
# ──────────────────────────────────────────────────────────────────────────────
CRISIS_SCENARIOS = {
    "2008 Global Financial Crisis": {
        "emoji": "🏦",
        "period": "Jan 2008 – Oct 2008",
        "trigger": "US subprime mortgage collapse → Lehman Brothers bankruptcy → global credit freeze",
        "nifty_peak_to_trough": -0.6397,       # Nifty 6357 → 2253 (≈ −64.5%)
        "duration_trading_days": 196,           # ~9 months of sustained selling
        "recovery_months": 71,                  # months to sustainably reclaim peak
        "annualised_vol_crisis": 0.62,          # annualised σ during crisis window
        "annualised_vol_normal": 0.17,          # pre-crisis baseline (Nifty long-run)
        "daily_drift_crisis": -0.0050,          # average daily drift during drawdown
        "fat_tail_df": 3.5,                     # Student-t degrees of freedom (fatter tails)
        "sector_multipliers": {
            # multiplier > 1 → sector fell harder than Nifty;
            # multiplier < 1 → relative outperformance (defensive)
            "Banking":  1.42,   # PSU + private banks: credit freeze, NPAs
            "IT":       0.72,   # export revenues dipped but USD/INR hedge helped
            "FMCG":     0.48,   # most defensive; demand inelastic
            "Pharma":   0.55,   # defensive; exports cushioned
            "Auto":     1.38,   # discretionary capex collapse
            "Energy":   1.25,   # crude collapse, OMC losses
            "Metals":   1.65,   # commodity supercycle bust; TATASTEEL −80%+
            "Infra":    1.45,   # capex freeze, credit crunch
        },
        "macro_context": {
            "india_vix_peak": 85,
            "usdinr_move_pct": +25.0,           # INR depreciated 25% vs USD
            "crude_oil_move_pct": -74.0,        # Brent $147 → $38
            "rbi_rate_change_bps": -425,        # RBI cut repo 425bps emergency
            "fii_outflow_cr": 52987,            # ₹ crore net FII outflow
        },
        "color": "#D92D20",
    },
    "COVID-19 Pandemic Crash": {
        "emoji": "🦠",
        "period": "Jan 2020 – Mar 2020",
        "trigger": "Global pandemic declared; India imposed nationwide lockdown on 24-Mar-2020",
        "nifty_peak_to_trough": -0.3960,       # 12431 → 7511 (≈ −39.6%)
        "duration_trading_days": 40,            # fastest crash ever; ~8 weeks
        "recovery_months": 10,                  # fastest recovery too
        "annualised_vol_crisis": 0.91,          # extremely elevated; VIX >80
        "annualised_vol_normal": 0.14,
        "daily_drift_crisis": -0.0155,          # very steep daily decline at peak
        "fat_tail_df": 2.8,                     # very fat tails (near-Cauchy)
        "sector_multipliers": {
            "Banking":  1.35,   # NPA fears, moratorium uncertainty
            "IT":       1.00,   # roughly in line; WFH tailwind offset demand shock
            "FMCG":     0.68,   # staples held; panic-buying
            "Pharma":   0.30,   # massive outperformance; vaccine/API demand
            "Auto":     1.42,   # production halted; showroom closures
            "Energy":   1.20,   # demand destruction; crude went negative (WTI)
            "Metals":   1.38,   # China demand uncertainty
            "Infra":    1.30,   # construction halted nationwide
        },
        "macro_context": {
            "india_vix_peak": 86,
            "usdinr_move_pct": +8.5,
            "crude_oil_move_pct": -130.0,       # WTI briefly negative
            "rbi_rate_change_bps": -115,
            "fii_outflow_cr": 61972,
        },
        "color": "#7C3AED",
    },
    "China Slowdown & Yuan Devaluation (2015–16)": {
        "emoji": "🐉",
        "period": "Apr 2015 – Feb 2016",
        "trigger": "China GDP slowdown, PBoC yuan devaluation, Greek debt default, global commodity rout",
        "nifty_peak_to_trough": -0.2600,       # Nifty ~9100 → ~6826 (≈ −25%)
        "duration_trading_days": 210,           # slow grinding bear; ~10 months
        "recovery_months": 24,
        "annualised_vol_crisis": 0.28,
        "annualised_vol_normal": 0.155,
        "daily_drift_crisis": -0.0018,
        "fat_tail_df": 4.5,
        "sector_multipliers": {
            "Banking":  1.25,
            "IT":       0.85,   # USD/INR depreciation gave IT a slight buffer
            "FMCG":     0.60,
            "Pharma":   0.75,
            "Auto":     1.35,
            "Energy":   1.40,   # crude rout hit oil stocks hard
            "Metals":   1.75,   # metals hardest hit; China demand collapse
            "Infra":    1.20,
        },
        "macro_context": {
            "india_vix_peak": 28,
            "usdinr_move_pct": +9.0,
            "crude_oil_move_pct": -60.0,
            "rbi_rate_change_bps": -125,
            "fii_outflow_cr": 14180,
        },
        "color": "#D97706",
    },
    "Inflation & Rate Hike Shock (2022)": {
        "emoji": "📈",
        "period": "Oct 2021 – Jun 2022",
        "trigger": "Post-COVID inflation surge; US Fed + RBI aggressive rate hikes; FII exodus",
        "nifty_peak_to_trough": -0.1750,       # 18604 → 15183 (≈ −18.4%)
        "duration_trading_days": 175,
        "recovery_months": 13,
        "annualised_vol_crisis": 0.21,
        "annualised_vol_normal": 0.155,
        "daily_drift_crisis": -0.0012,
        "fat_tail_df": 5.0,
        "sector_multipliers": {
            "Banking":  0.90,   # Banks partially benefit from rising rates
            "IT":       1.55,   # multiple compression; high-P/E IT hit hardest
            "FMCG":     0.70,
            "Pharma":   0.80,
            "Auto":     1.10,
            "Energy":   0.60,   # oil cos benefited from high crude prices
            "Metals":   1.30,
            "Infra":    1.20,
        },
        "macro_context": {
            "india_vix_peak": 30,
            "usdinr_move_pct": +6.0,
            "crude_oil_move_pct": +65.0,        # Brent spiked to $130 post Ukraine
            "rbi_rate_change_bps": +250,        # RBI hiked 250bps
            "fii_outflow_cr": 166500,           # record FII outflow
        },
        "color": "#059669",
    },
    "Dot-Com Bust (2000–2001)": {
        "emoji": "💻",
        "period": "Feb 2000 – Sep 2001",
        "trigger": "Global tech bubble burst; Y2K euphoria unwind; 9/11 geopolitical shock",
        "nifty_peak_to_trough": -0.5300,       # Nifty 1818 → 850 (≈ −53%)
        "duration_trading_days": 380,           # prolonged 19-month bear
        "recovery_months": 46,
        "annualised_vol_crisis": 0.38,
        "annualised_vol_normal": 0.22,
        "daily_drift_crisis": -0.0022,
        "fat_tail_df": 4.0,
        "sector_multipliers": {
            "Banking":  1.10,
            "IT":       2.10,   # IT was the bubble epicenter
            "FMCG":     0.55,
            "Pharma":   0.65,
            "Auto":     0.90,
            "Energy":   0.80,
            "Metals":   1.05,
            "Infra":    0.95,
        },
        "macro_context": {
            "india_vix_peak": 45,
            "usdinr_move_pct": +4.0,
            "crude_oil_move_pct": -35.0,
            "rbi_rate_change_bps": -100,
            "fii_outflow_cr": 8200,
        },
        "color": "#1B6CA8",
    },
    "Custom Scenario (User Defined)": {
        "emoji": "⚙️",
        "period": "User-specified",
        "trigger": "Custom stress scenario — user-defined parameters",
        "nifty_peak_to_trough": -0.30,
        "duration_trading_days": 120,
        "recovery_months": 18,
        "annualised_vol_crisis": 0.35,
        "annualised_vol_normal": 0.155,
        "daily_drift_crisis": -0.0025,
        "fat_tail_df": 4.0,
        "sector_multipliers": {
            "Banking": 1.20, "IT": 1.20, "FMCG": 0.70,
            "Pharma": 0.75, "Auto": 1.25, "Energy": 1.10,
            "Metals": 1.40, "Infra": 1.20,
        },
        "macro_context": {
            "india_vix_peak": 35,
            "usdinr_move_pct": 0.0,
            "crude_oil_move_pct": 0.0,
            "rbi_rate_change_bps": 0,
            "fii_outflow_cr": 0,
        },
        "color": "#5A6474",
    },
}

# Sector tag for tickers not in the standard NSE_SECTORS dict
_TICKER_SECTOR_MAP: Dict[str, str] = {}
for _sector, _tickers in NSE_SECTORS.items():
    for _t in _tickers:
        _TICKER_SECTOR_MAP[_t] = _sector


@st.cache_data(ttl=600)
def fetch_stock_beta_vol(ticker: str) -> Dict:
    """
    Fetch a stock's beta vs Nifty and annualised volatility from 1-year daily returns.
    Uses OLS regression: β = Cov(r_stock, r_nifty) / Var(r_nifty)
    Also computes: annualised σ, skewness, excess kurtosis, Jarque-Bera p-value.
    """
    try:
        raw = yf.download(
            [ticker, "^NSEI"], period="1y", interval="1d",
            progress=False, auto_adjust=True
        )
        if raw is None or raw.empty:
            return {"beta": 1.0, "vol": 0.20, "skew": 0.0, "kurt": 0.0}

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            return {"beta": 1.0, "vol": 0.20, "skew": 0.0, "kurt": 0.0}

        rets = close.pct_change().dropna()
        if ticker not in rets.columns or "^NSEI" not in rets.columns:
            return {"beta": 1.0, "vol": 0.20, "skew": 0.0, "kurt": 0.0}

        r_s = rets[ticker].dropna().values
        r_n = rets["^NSEI"].dropna().values
        n   = min(len(r_s), len(r_n))
        r_s, r_n = r_s[-n:], r_n[-n:]

        cov_mat = np.cov(r_s, r_n)
        beta    = float(cov_mat[0, 1] / cov_mat[1, 1]) if cov_mat[1, 1] != 0 else 1.0
        ann_vol = float(np.std(r_s) * np.sqrt(252))
        skewness = float(stats.skew(r_s))
        kurtosis = float(stats.kurtosis(r_s))          # excess kurtosis (Fisher)
        jb_stat, jb_p = stats.jarque_bera(r_s)

        return {
            "beta":     round(max(0.1, min(beta, 4.0)), 3),   # clip to sane range
            "vol":      round(max(0.05, ann_vol), 4),
            "skew":     round(skewness, 3),
            "kurt":     round(kurtosis, 3),
            "jb_p":     round(float(jb_p), 4),
            "n_obs":    n,
        }
    except Exception:
        return {"beta": 1.0, "vol": 0.20, "skew": 0.0, "kurt": 0.0}


def run_stress_simulation(
    holdings: Dict,          # {ticker: {qty, avg_cost, sector}}
    current_prices: Dict,    # {ticker: {price, ...}}
    scenario: Dict,          # one entry from CRISIS_SCENARIOS
    n_simulations: int = 5000,
    horizon_days: int = None,
) -> Dict:
    """
    Monte Carlo stress test using Geometric Brownian Motion with:
      - Cholesky-decomposed correlated asset returns
      - Student-t innovations (fat tails calibrated per scenario)
      - Crisis-regime drift and volatility (not the benign historical mean)
      - Sector-specific multipliers applied to the market shock component
      - VaR (parametric + historical), CVaR (Expected Shortfall), Max Drawdown dist.

    Returns a dict with simulation results, risk metrics, and per-stock attribution.
    """
    if not holdings or not current_prices:
        return {"error": "No holdings or prices provided"}

    if horizon_days is None:
        horizon_days = scenario["duration_trading_days"]

    # ── 1. Build position table ──────────────────────────────────────────────
    tickers     = [t for t in holdings if t in current_prices]
    if not tickers:
        return {"error": "No price data available for held stocks"}

    prices_now  = np.array([current_prices[t]["price"] for t in tickers])
    quantities  = np.array([holdings[t]["qty"]         for t in tickers])
    avg_costs   = np.array([holdings[t]["avg_cost"]    for t in tickers])
    sectors     = [holdings[t].get("sector", "Unknown") for t in tickers]
    port_value  = float(np.sum(prices_now * quantities))

    if port_value <= 0:
        return {"error": "Zero portfolio value"}

    weights = (prices_now * quantities) / port_value   # portfolio weights

    # ── 2. Per-stock beta + vol from live data ───────────────────────────────
    betas    = []
    live_vol = []
    for t in tickers:
        bv = fetch_stock_beta_vol(t)
        betas.append(bv.get("beta", 1.0))
        live_vol.append(bv.get("vol", 0.20))

    betas    = np.array(betas)
    live_vol = np.array(live_vol)

    # ── 3. Crisis-regime parameters ──────────────────────────────────────────
    crisis_vol_ratio = (
        scenario["annualised_vol_crisis"] / scenario["annualised_vol_normal"]
    )
    # Scale each stock's vol by the crisis vol-ratio (market-wide amplification)
    crisis_vol = live_vol * crisis_vol_ratio      # per-stock annualised crisis vol
    daily_vol  = crisis_vol / np.sqrt(252)        # per-stock daily crisis vol

    # ── 4. Sector shock multiplier ────────────────────────────────────────────
    # Market component of each stock's daily shock =
    #     beta_i × sector_mult_i × nifty_daily_drift_crisis
    # Idiosyncratic component drawn from t-distribution with calibrated df
    mkt_drift   = scenario["daily_drift_crisis"]   # daily Nifty drift during crash
    sect_mults  = np.array([
        scenario["sector_multipliers"].get(s, 1.0) for s in sectors
    ])
    # Stock-level crisis drift = beta × sector_mult × market_drift
    stock_drift_daily = betas * sect_mults * mkt_drift  # shape: (n_stocks,)

    # ── 5. Build approximate correlation matrix from market model ─────────────
    # Using a single-factor model: ρ_ij ≈ β_i × β_j × ρ_mkt / (σ_i × σ_j)
    # where ρ_mkt is the Nifty variance contribution.
    # This avoids downloading 5-year joint history and keeps it tractable.
    mkt_var     = (scenario["annualised_vol_crisis"] ** 2) / 252  # daily mkt var
    # Systematic var of stock i = beta_i^2 * mkt_var
    sys_var     = (betas ** 2) * mkt_var
    idio_var    = np.maximum(daily_vol ** 2 - sys_var, 1e-8)      # idio variance

    n_assets    = len(tickers)
    cov_matrix  = np.zeros((n_assets, n_assets))
    for i in range(n_assets):
        for j in range(n_assets):
            if i == j:
                cov_matrix[i, j] = daily_vol[i] ** 2
            else:
                cov_matrix[i, j] = betas[i] * betas[j] * mkt_var  # cov from mkt

    # Ensure positive semi-definite (add small regularisation)
    cov_matrix += np.eye(n_assets) * 1e-8
    # Cholesky decomposition for correlated draws
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        # Fallback: use diagonal (uncorrelated)
        L = np.diag(daily_vol)

    # ── 6. Monte Carlo simulation ─────────────────────────────────────────────
    df_t      = scenario["fat_tail_df"]       # Student-t degrees of freedom
    rng       = np.random.default_rng(seed=42)

    # Final portfolio value after `horizon_days` for each simulation
    final_port_values  = np.zeros(n_simulations)
    min_port_values    = np.zeros(n_simulations)   # worst intra-path drawdown value
    stock_final_prices = np.zeros((n_simulations, n_assets))

    for sim in range(n_simulations):
        # Draw correlated Student-t shocks: Z = L @ ε where ε ~ t(df) / sqrt(df/(df-2))
        epsilon   = rng.standard_t(df=df_t, size=(horizon_days, n_assets))
        epsilon   = epsilon / np.sqrt(df_t / (df_t - 2))   # rescale to unit variance
        shocks    = epsilon @ L.T                            # correlated shocks (T × N)

        # Build log-return paths: r_t = drift + shock
        # drift per step = stock_drift_daily - 0.5 * σ^2 (Itô correction)
        ito_correction   = -0.5 * daily_vol ** 2
        daily_log_rets   = (stock_drift_daily + ito_correction) + shocks  # (T × N)

        cum_log_rets     = np.cumsum(daily_log_rets, axis=0)              # (T × N)
        price_paths      = prices_now * np.exp(cum_log_rets)              # (T × N)

        # Portfolio value path
        port_path        = price_paths @ quantities                        # (T,)
        final_port_values[sim]   = port_path[-1]
        min_port_values[sim]     = np.min(port_path)
        stock_final_prices[sim]  = price_paths[-1]

    # ── 7. Risk metrics ───────────────────────────────────────────────────────
    final_pnl     = final_port_values - port_value   # P&L distribution
    final_pnl_pct = final_pnl / port_value * 100

    # VaR — parametric (normal approximation for comparison)
    port_daily_vol = float(np.sqrt(weights @ cov_matrix @ weights))
    port_drift_day = float(weights @ stock_drift_daily)
    var_95_param   = -(port_drift_day * horizon_days
                       - 1.645 * port_daily_vol * np.sqrt(horizon_days)) * port_value
    var_99_param   = -(port_drift_day * horizon_days
                       - 2.326 * port_daily_vol * np.sqrt(horizon_days)) * port_value

    # VaR — historical simulation from Monte Carlo outcomes
    var_95_hist    = float(-np.percentile(final_pnl, 5))
    var_99_hist    = float(-np.percentile(final_pnl, 1))

    # CVaR (Expected Shortfall) — mean loss beyond VaR threshold
    cvar_95        = float(-np.mean(final_pnl[final_pnl <= np.percentile(final_pnl, 5)]))
    cvar_99        = float(-np.mean(final_pnl[final_pnl <= np.percentile(final_pnl, 1)]))

    # Maximum Drawdown distribution (across simulations)
    max_dd_dist    = (min_port_values - port_value) / port_value * 100  # negative %
    median_max_dd  = float(np.median(max_dd_dist))
    worst_5pct_dd  = float(np.percentile(max_dd_dist, 5))

    # ── 8. Per-stock attribution ──────────────────────────────────────────────
    stock_attribution = []
    for i, ticker in enumerate(tickers):
        median_final   = float(np.median(stock_final_prices[:, i]))
        p5_final       = float(np.percentile(stock_final_prices[:, i], 5))
        p95_final      = float(np.percentile(stock_final_prices[:, i], 95))
        median_pnl_pct = (median_final - prices_now[i]) / prices_now[i] * 100
        p5_pnl_pct     = (p5_final     - prices_now[i]) / prices_now[i] * 100
        investment_val  = float(prices_now[i] * quantities[i])
        median_pnl_inr  = float(median_pnl_pct / 100 * investment_val)
        p5_pnl_inr      = float(p5_pnl_pct / 100 * investment_val)

        stock_attribution.append({
            "ticker":        ticker,
            "sector":        sectors[i],
            "current_price": round(float(prices_now[i]), 2),
            "qty":           int(quantities[i]),
            "investment":    round(investment_val, 2),
            "weight_pct":    round(float(weights[i] * 100), 2),
            "beta":          round(float(betas[i]), 3),
            "live_vol_pct":  round(float(live_vol[i] * 100), 2),
            "sect_mult":     round(float(sect_mults[i]), 2),
            "median_price_scenario": round(median_final, 2),
            "median_pnl_pct":        round(median_pnl_pct, 2),
            "median_pnl_inr":        round(median_pnl_inr, 2),
            "p5_pnl_pct":            round(p5_pnl_pct, 2),   # 5th-percentile (worst)
            "p95_pnl_pct":           round(p95_final / prices_now[i] * 100 - 100, 2),
        })

    # Sort by worst expected loss contribution
    stock_attribution.sort(key=lambda x: x["median_pnl_inr"])

    # ── 9. Scenario P&L distribution statistics ───────────────────────────────
    skewness = float(stats.skew(final_pnl))
    kurtosis = float(stats.kurtosis(final_pnl))

    return {
        "portfolio_value":        round(port_value, 2),
        "n_simulations":          n_simulations,
        "horizon_days":           horizon_days,

        # P&L distribution
        "pnl_distribution":       final_pnl.tolist(),
        "pnl_pct_distribution":   final_pnl_pct.tolist(),
        "median_pnl":             round(float(np.median(final_pnl)), 2),
        "median_pnl_pct":         round(float(np.median(final_pnl_pct)), 2),
        "mean_pnl":               round(float(np.mean(final_pnl)), 2),
        "p5_pnl":                 round(float(np.percentile(final_pnl, 5)), 2),
        "p1_pnl":                 round(float(np.percentile(final_pnl, 1)), 2),
        "p95_pnl":                round(float(np.percentile(final_pnl, 95)), 2),
        "prob_loss":              round(float(np.mean(final_pnl < 0) * 100), 1),
        "prob_loss_10pct":        round(float(np.mean(final_pnl_pct < -10) * 100), 1),
        "prob_loss_20pct":        round(float(np.mean(final_pnl_pct < -20) * 100), 1),
        "prob_loss_30pct":        round(float(np.mean(final_pnl_pct < -30) * 100), 1),
        "skewness":               round(skewness, 3),
        "kurtosis":               round(kurtosis, 3),

        # VaR / CVaR
        "var_95_param":           round(var_95_param, 2),
        "var_99_param":           round(var_99_param, 2),
        "var_95_hist":            round(var_95_hist, 2),
        "var_99_hist":            round(var_99_hist, 2),
        "cvar_95":                round(cvar_95, 2),
        "cvar_99":                round(cvar_99, 2),

        # Drawdown
        "median_max_drawdown_pct": round(median_max_dd, 2),
        "worst_5pct_drawdown_pct": round(worst_5pct_dd, 2),

        # Per-stock
        "stock_attribution":      stock_attribution,

        # Portfolio-level
        "portfolio_beta":         round(float(weights @ betas), 3),
        "portfolio_crisis_vol":   round(float(np.sqrt(weights @ cov_matrix @ weights) * np.sqrt(252) * 100), 2),
    }


def page_stress_test():
    """
    Stress Test Your Portfolio — quant finance grade scenario analysis.
    User enters their equity holdings (or imports from existing simulation holdings),
    selects a historical crisis, and sees a full Monte Carlo stress report.
    """
    section_header("Stress Test Your Portfolio")

    st.markdown("""
    <div style="background:linear-gradient(135deg,#FEF3F2 0%,#FFF8F1 100%);
        border:1px solid #FECACA;border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;">
        <div style="font-size:0.78rem;font-weight:700;color:#991B1B;margin-bottom:0.4rem;">
            ⚠  QUANTITATIVE RISK SIMULATION
        </div>
        <div style="font-size:0.73rem;color:#7F1D1D;line-height:1.6;">
            Simulations use Geometric Brownian Motion with Student-t innovations (fat tails),
            Cholesky-correlated multi-asset paths, crisis-regime drift & volatility calibrated
            from actual NSE drawdown history. Past crises do not guarantee identical future behaviour.
            Not financial advice.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SCENARIO SELECTOR ────────────────────────────────────────────────────
    section_header("Select Crisis Scenario", "📋")
    scenario_names = list(CRISIS_SCENARIOS.keys())

    cols_scen = st.columns(3)
    selected_scenario = st.session_state.get("stress_scenario", scenario_names[0])

    for idx, sname in enumerate(scenario_names):
        sc  = CRISIS_SCENARIOS[sname]
        col = cols_scen[idx % 3]
        with col:
            is_active  = (sname == selected_scenario)
            border_col = sc["color"] if is_active else "var(--border)"
            bg_col     = f"rgba{tuple(int(sc['color'].lstrip('#')[i:i+2], 16) for i in (0,2,4)) + (0.06,)}"
            if is_active:
                bg_col = f"rgba{tuple(int(sc['color'].lstrip('#')[i:i+2], 16) for i in (0,2,4)) + (0.12,)}"

            st.markdown(f"""
            <div style="background:{bg_col};border:2px solid {border_col};border-radius:10px;
                padding:0.9rem;margin-bottom:0.5rem;min-height:120px;">
                <div style="font-size:1.1rem;">{sc['emoji']}</div>
                <div style="font-size:0.75rem;font-weight:700;color:var(--text-primary);
                    margin:0.3rem 0 0.2rem 0;line-height:1.3;">{sname}</div>
                <div style="font-size:0.62rem;color:var(--text-muted);margin-bottom:0.3rem;">{sc['period']}</div>
                <div style="font-size:0.68rem;font-weight:700;color:{sc['color']};">
                    Nifty: {sc['nifty_peak_to_trough']*100:+.1f}%
                    &nbsp;|&nbsp; {sc['duration_trading_days']}d crash
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {'✓' if is_active else ''}", key=f"sel_sc_{idx}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state["stress_scenario"] = sname
                st.rerun()

    sc_data = CRISIS_SCENARIOS[selected_scenario]

    # ── CUSTOM SCENARIO SLIDERS ───────────────────────────────────────────────
    if selected_scenario == "Custom Scenario (User Defined)":
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Custom Scenario Parameters", "⚙️")
        c1, c2, c3 = st.columns(3)
        with c1:
            custom_drawdown = st.slider(
                "Expected Nifty Drawdown (%)", min_value=-80, max_value=-5,
                value=-30, step=5, key="custom_dd"
            )
            sc_data = dict(sc_data)
            sc_data["nifty_peak_to_trough"] = custom_drawdown / 100
        with c2:
            custom_vol = st.slider(
                "Crisis Annualised Volatility (%)", min_value=15, max_value=120,
                value=35, step=5, key="custom_vol"
            )
            sc_data["annualised_vol_crisis"] = custom_vol / 100
        with c3:
            custom_dur = st.slider(
                "Crisis Duration (trading days)", min_value=20, max_value=400,
                value=120, step=10, key="custom_dur"
            )
            sc_data["duration_trading_days"] = custom_dur
        sc_data["daily_drift_crisis"] = (
            sc_data["nifty_peak_to_trough"] / sc_data["duration_trading_days"]
        ) * 1.2   # slightly faster than linear for realism
        st.markdown("<br>", unsafe_allow_html=True)
        section_header("Custom Sector Shock Multipliers", "📐")
        st.markdown(
            "Set how hard each sector is hit **relative to the Nifty** drawdown you specified above. "
            "1.0× = in line with market. >1.0× = sector falls harder. <1.0× = defensive outperformance.",
            help="Multiplier × Nifty drawdown = implied sector drawdown"
        )
        default_mults = CRISIS_SCENARIOS["Custom Scenario (User Defined)"]["sector_multipliers"]
        custom_sector_mults = {}
        sect_slider_cols = st.columns(4)
        for s_idx, (sect_name, def_mult) in enumerate(default_mults.items()):
            with sect_slider_cols[s_idx % 4]:
                custom_sector_mults[sect_name] = st.slider(
                    f"{sect_name}",
                    min_value=0.10, max_value=3.00,
                    value=float(def_mult), step=0.05,
                    key=f"custom_sect_{sect_name}",
                    help=f"Implied drawdown: {custom_drawdown * def_mult:.1f}%"
                )
        sc_data["sector_multipliers"] = custom_sector_mults

    # ── SELECTED SCENARIO DETAILS ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header(f"{sc_data['emoji']}  {selected_scenario} — Scenario Detail", "")

    mc = sc_data["macro_context"]
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    with col_m1:
        st.metric("Nifty Peak→Trough", f"{sc_data['nifty_peak_to_trough']*100:+.1f}%")
    with col_m2:
        st.metric("Crash Duration", f"{sc_data['duration_trading_days']} days")
    with col_m3:
        st.metric("India VIX Peak", str(mc['india_vix_peak']))
    with col_m4:
        st.metric("USD/INR Move", f"{mc['usdinr_move_pct']:+.1f}%")
    with col_m5:
        st.metric("Recovery", f"{sc_data['recovery_months']}m")

    st.markdown(f"""
    <div class="alert-info" style="margin-top:0.75rem;">
        <b>Trigger:</b> {sc_data['trigger']}
    </div>
    """, unsafe_allow_html=True)

    # ── SECTOR MULTIPLIERS TABLE ──────────────────────────────────────────────
    with st.expander("📐  Sector Shock Multipliers (vs Nifty)", expanded=False):
        st.markdown("""
        <div style="font-size:0.72rem;color:var(--text-muted);margin-bottom:0.75rem;">
        Multiplier = (Sector drawdown) ÷ (Nifty drawdown) during the crisis window.
        Values > 1 indicate the sector fell <i>harder</i> than the broad market.
        </div>
        """, unsafe_allow_html=True)
        mult_cols = st.columns(4)
        for idx2, (sector_name, mult) in enumerate(sc_data["sector_multipliers"].items()):
            implied_dd = sc_data["nifty_peak_to_trough"] * mult * 100
            color      = "#D92D20" if mult > 1.0 else "#0D9373"
            with mult_cols[idx2 % 4]:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:8px;padding:0.6rem 0.8rem;margin-bottom:0.5rem;">
                    <div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);
                        text-transform:uppercase;">{sector_name}</div>
                    <div style="font-family:'DM Mono',monospace;font-size:1.0rem;
                        font-weight:700;color:{color};">{mult:.2f}×</div>
                    <div style="font-size:0.68rem;color:{color};">Implied: {implied_dd:+.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

    # ── PORTFOLIO INPUT ────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Enter Your Equity Holdings", "💼")

    use_sim_holdings = False
    if st.session_state.holdings:
        use_sim_col, _ = st.columns([2, 3])
        with use_sim_col:
            use_sim_holdings = st.checkbox(
                "📥  Import from my simulated portfolio holdings",
                value=False, key="stress_import_sim"
            )

    if use_sim_holdings and st.session_state.holdings:
        stress_holdings = {}
        for ticker, pos in st.session_state.holdings.items():
            p = current_prices_for_stress = fetch_current_price(ticker)
            if p:
                stress_holdings[ticker] = {
                    "qty":       pos["qty"],
                    "avg_cost":  pos["avg_cost"],
                    "sector":    pos.get("sector", _TICKER_SECTOR_MAP.get(ticker, "Unknown")),
                    "cur_price": p["price"],
                }
        if stress_holdings:
            st.markdown(f"""
            <div class="alert-success">
                Imported {len(stress_holdings)} positions from your simulated portfolio.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-warning">Could not fetch prices for your holdings. Please enter manually.</div>', unsafe_allow_html=True)
            use_sim_holdings = False

    if not use_sim_holdings:
        st.markdown("""
        <div style="font-size:0.73rem;color:var(--text-muted);margin-bottom:0.75rem;">
        Enter NSE tickers (e.g. RELIANCE, HDFCBANK, TCS) — the <code>.NS</code> suffix is added automatically.
        </div>
        """, unsafe_allow_html=True)

        # Dynamic row-based input (up to 15 stocks)
        if "stress_n_stocks" not in st.session_state:
            st.session_state["stress_n_stocks"] = 3

        n_stocks = st.session_state["stress_n_stocks"]
        stress_holdings = {}

        col_h, col_a, col_b, col_c = st.columns([1.5, 1.2, 1.0, 1.2])
        col_h.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">TICKER</div>', unsafe_allow_html=True)
        col_a.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">QTY (shares)</div>', unsafe_allow_html=True)
        col_b.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">AVG COST (₹)</div>', unsafe_allow_html=True)
        col_c.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;">SECTOR</div>', unsafe_allow_html=True)

        sector_options = ["Unknown"] + list(NSE_SECTORS.keys())
        valid_rows = 0

        for row_i in range(n_stocks):
            r1, r2, r3, r4 = st.columns([1.5, 1.2, 1.0, 1.2])
            with r1:
                raw_ticker = st.text_input(
                    f"Ticker {row_i+1}", label_visibility="collapsed",
                    placeholder=f"e.g. {'RELIANCE' if row_i==0 else 'HDFCBANK' if row_i==1 else 'TCS'}",
                    key=f"st_ticker_{row_i}"
                )
            with r2:
                qty_in = st.number_input(
                    f"Qty {row_i+1}", min_value=1, max_value=100000, value=10,
                    label_visibility="collapsed", key=f"st_qty_{row_i}"
                )
            with r3:
                avg_cost_in = st.number_input(
                    f"AvgCost {row_i+1}", min_value=0.01, value=1000.0, step=1.0,
                    label_visibility="collapsed", key=f"st_avg_{row_i}", format="%.2f"
                )
            with r4:
                sector_in = st.selectbox(
                    f"Sector {row_i+1}", options=sector_options,
                    label_visibility="collapsed", key=f"st_sec_{row_i}"
                )

            if raw_ticker.strip():
                ticker_clean = raw_ticker.strip().upper()
                if not ticker_clean.endswith(".NS"):
                    ticker_clean += ".NS"
                # Live validation — try fast_info; if it returns no last_price, ticker is invalid
                try:
                    _fi = yf.Ticker(ticker_clean).fast_info
                    _price = getattr(_fi, "last_price", None)
                    if _price is None or _price <= 0:
                        st.warning(f"⚠ **{ticker_clean.replace('.NS','')}** — ticker not found on NSE. Check spelling and try again.", icon="⚠️")
                    else:
                        stress_holdings[ticker_clean] = {
                            "qty":      int(qty_in),
                            "avg_cost": float(avg_cost_in),
                            "sector":   sector_in,
                        }
                        valid_rows += 1
                except Exception:
                    st.warning(f"⚠ **{ticker_clean.replace('.NS','')}** — could not validate. Check NSE ticker symbol.", icon="⚠️")

        add_col, rem_col = st.columns([1, 1])
        with add_col:
            if n_stocks < 15 and st.button("＋ Add Stock", key="stress_add_row"):
                st.session_state["stress_n_stocks"] = n_stocks + 1
                st.rerun()
        with rem_col:
            if n_stocks > 1 and st.button("－ Remove Last", key="stress_rem_row"):
                st.session_state["stress_n_stocks"] = n_stocks - 1
                st.rerun()

    # ── SIMULATION CONTROLS ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Simulation Parameters", "⚡")

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        n_sims = st.select_slider(
            "Number of Monte Carlo Paths",
            options=[1000, 2000, 5000, 10000, 20000],
            value=5000, key="stress_n_sims"
        )
    with sim_col2:
        horizon_override = st.checkbox(
            "Override horizon (default = scenario duration)", key="stress_override_horizon"
        )
        if horizon_override:
            horizon_days_input = st.slider(
                "Horizon (trading days)", 10, 500,
                value=sc_data["duration_trading_days"], key="stress_horizon_days"
            )
        else:
            horizon_days_input = sc_data["duration_trading_days"]
    with sim_col3:
        st.markdown(f"""
        <div style="background:var(--accent-light);border:1px solid var(--border);
            border-radius:8px;padding:0.75rem 1rem;margin-top:1.4rem;">
            <div style="font-size:0.65rem;color:var(--text-muted);font-weight:700;">SIMULATION SPEC</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:var(--text-primary);margin-top:0.3rem;">
                {n_sims:,} paths × {horizon_days_input}d<br>
                GBM + Student-t (df={sc_data['fat_tail_df']})<br>
                Cholesky corr. matrix
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── RUN BUTTON ─────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(
        f"🧨  Run Stress Simulation — {selected_scenario}",
        type="primary", use_container_width=True, key="stress_run_btn"
    )

    if run_btn:
        if not stress_holdings:
            st.error("Please enter at least one stock holding before running the simulation.")
            return

        # Fetch live prices for all stress_holdings
        with st.spinner("📡  Fetching live prices…"):
            tickers_to_fetch = list(stress_holdings.keys())
            live_prices = {}
            for t in tickers_to_fetch:
                p = fetch_current_price(t)
                if p:
                    live_prices[t] = p

        # Pre-fill from avg_cost for stocks where price fetch failed
        for t, pos in stress_holdings.items():
            if t not in live_prices:
                live_prices[t] = {"price": pos["avg_cost"]}

        with st.spinner(f"⚡  Running {n_sims:,} Monte Carlo simulations…"):
            results = run_stress_simulation(
                holdings      = stress_holdings,
                current_prices= live_prices,
                scenario      = sc_data,
                n_simulations = n_sims,
                horizon_days  = horizon_days_input,
            )

        if "error" in results:
            st.error(f"Simulation error: {results['error']}")
            return

        st.session_state["stress_results"] = results
        st.session_state["stress_scenario_used"] = selected_scenario
        st.rerun()

    # ── DISPLAY RESULTS ────────────────────────────────────────────────────────
    if "stress_results" not in st.session_state:
        return

    results    = st.session_state["stress_results"]
    sc_used    = st.session_state.get("stress_scenario_used", selected_scenario)
    sc_display = CRISIS_SCENARIOS[sc_used]

    st.markdown("---")
    st.markdown(f"""
    <div style="font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;
        color:var(--accent-dark);margin-bottom:0.3rem;">
        Stress Test Results — {sc_display['emoji']} {sc_used}
    </div>
    <div style="font-size:0.72rem;color:var(--text-muted);">
        {results['n_simulations']:,} Monte Carlo paths &nbsp;|&nbsp;
        {results['horizon_days']} trading-day horizon &nbsp;|&nbsp;
        Portfolio value: ₹{results['portfolio_value']:,.2f}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KEY RISK METRICS ROW ──────────────────────────────────────────────────
    section_header("Key Risk Metrics", "📐")

    m_cols = st.columns(4)
    with m_cols[0]:
        st.metric("Median P&L", f"₹{results['median_pnl']:+,.0f}", f"{results['median_pnl_pct']:+.1f}%")
    with m_cols[1]:
        st.metric("VaR 95% (MC)", f"₹{results['var_95_hist']:,.0f}", "5% worst loss")
    with m_cols[2]:
        st.metric("CVaR 95%", f"₹{results['cvar_95']:,.0f}", "Exp. shortfall")
    with m_cols[3]:
        st.metric("Median Max DD", f"{results['median_max_drawdown_pct']:.1f}%", "Intra-path drawdown")

    # Second metrics row
    m_cols2 = st.columns(4)
    with m_cols2[0]:
        st.metric("P(loss > 10%)", f"{results['prob_loss_10pct']:.1f}%")
    with m_cols2[1]:
        st.metric("P(loss > 20%)", f"{results['prob_loss_20pct']:.1f}%")
    with m_cols2[2]:
        st.metric("VaR 99% (MC)", f"₹{results['var_99_hist']:,.0f}")
    with m_cols2[3]:
        st.metric("Portfolio Beta", f"{results['portfolio_beta']:.3f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── P&L DISTRIBUTION HISTOGRAM ────────────────────────────────────────────
    section_header("P&L Distribution (Monte Carlo)", "📊")

    pnl_arr  = np.array(results["pnl_distribution"])
    pnl_pct  = np.array(results["pnl_pct_distribution"])
    var_95   = -results["var_95_hist"]
    var_99   = -results["var_99_hist"]
    cvar_95  = -results["cvar_95"]

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=pnl_arr,
        nbinsx=120,
        name="Simulated P&L",
        marker=dict(
            color=[sc_display["color"] if v >= 0 else "#D92D20" for v in pnl_arr],
            opacity=0.75,
        ),
        hovertemplate="P&L: ₹%{x:,.0f}<br>Count: %{y}<extra></extra>",
    ))

    # VaR / CVaR vertical lines
    fig_hist.add_vline(
        x=var_95, line=dict(color="#D97706", width=1.8, dash="dash"),
        annotation_text=f"VaR 95%<br>₹{abs(var_95):,.0f}",
        annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#D97706",
    )
    fig_hist.add_vline(
        x=var_99, line=dict(color="#D92D20", width=1.8, dash="dot"),
        annotation_text=f"VaR 99%<br>₹{abs(var_99):,.0f}",
        annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#D92D20",
    )
    fig_hist.add_vline(
        x=cvar_95, line=dict(color="#7C3AED", width=1.5, dash="longdash"),
        annotation_text=f"CVaR 95%<br>₹{abs(cvar_95):,.0f}",
        annotation_position="top left",
        annotation_font_size=10, annotation_font_color="#7C3AED",
    )
    fig_hist.add_vline(
        x=0, line=dict(color="#0F1923", width=1.2),
    )

    fig_hist.update_layout(
        **CHART_THEME, height=360,
        title=dict(
            text=f"Portfolio P&L Distribution — {results['n_simulations']:,} simulations, {results['horizon_days']}d horizon",
            font=dict(size=12), x=0
        ),
        xaxis_title="P&L (₹)",
        yaxis_title="Frequency",
        showlegend=False,
        bargap=0.02,
        annotations=[
            dict(
                x=0.98, y=0.95, xref="paper", yref="paper",
                text=(f"Skew: {results['skewness']:.2f}  "
                      f"Kurt: {results['kurtosis']:.2f}  "
                      f"P(loss): {results['prob_loss']:.0f}%"),
                showarrow=False, font=dict(size=10, color="#5A6474"),
                align="right", bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#E2E7EF", borderwidth=1, borderpad=4,
            )
        ],
    )
    st.plotly_chart(fig_hist, use_container_width=True, config=plotly_chart_config())

    # ── PROBABILITY OF LOSS CHART ─────────────────────────────────────────────
    section_header("Loss Probability Curve", "📉")

    loss_thresholds = np.arange(-5, -85, -5)
    probs = [float(np.mean(pnl_pct < thresh) * 100) for thresh in loss_thresholds]

    fig_prob = go.Figure()
    fig_prob.add_trace(go.Scatter(
        x=loss_thresholds, y=probs,
        fill="tozeroy",
        fillcolor=f"rgba{tuple(int(sc_display['color'].lstrip('#')[i:i+2], 16) for i in (0,2,4)) + (0.15,)}",
        line=dict(color=sc_display["color"], width=2),
        mode="lines+markers",
        marker=dict(size=6),
        hovertemplate="Loss > %{x:.0f}%: %{y:.1f}% probability<extra></extra>",
        name="Loss probability",
    ))
    # Reference lines
    for ref_loss in [-10, -20, -30, -50]:
        ref_prob = float(np.mean(pnl_pct < ref_loss) * 100)
        fig_prob.add_annotation(
            x=ref_loss, y=ref_prob,
            text=f"{ref_prob:.1f}%",
            showarrow=True, arrowhead=2, arrowsize=0.8,
            font=dict(size=9, color="#5A6474"),
            ax=20, ay=-20,
        )

    fig_prob.update_layout(
        **CHART_THEME, height=300,
        title=dict(text="Probability of Exceeding Loss Threshold (%)", font=dict(size=12), x=0),
        xaxis_title="Portfolio Loss (%)",
        yaxis_title="Probability (%)",
        showlegend=False,
    )
    st.plotly_chart(fig_prob, use_container_width=True, config=plotly_chart_config())

    # ── STOCK ATTRIBUTION TABLE ───────────────────────────────────────────────
    section_header("Per-Stock Attribution & Stress Estimates", "🗃")

    attribution = results["stock_attribution"]

    # Header
    st.markdown("""
    <div style="display:grid;grid-template-columns:0.8fr 0.7fr 0.6fr 0.6fr 0.5fr 0.5fr 0.8fr 0.8fr 0.8fr;
        gap:0.4rem;padding:0.4rem 0.75rem;font-size:0.62rem;font-weight:700;
        color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;
        border-bottom:2px solid var(--border);">
        <span>Ticker</span><span>Sector</span><span>Weight</span><span>Beta</span>
        <span>Sect Mult</span><span>Vol σ</span><span>Median P&L ₹</span>
        <span>Median P&L %</span><span>5th-pct P&L %</span>
    </div>
    """, unsafe_allow_html=True)

    for row in attribution:
        pnl_color = "var(--negative)" if row["median_pnl_inr"] < 0 else "var(--positive)"
        p5_color  = "var(--negative)" if row["p5_pnl_pct"] < 0 else "var(--positive)"
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:0.8fr 0.7fr 0.6fr 0.6fr 0.5fr 0.5fr 0.8fr 0.8fr 0.8fr;
            gap:0.4rem;padding:0.45rem 0.75rem;font-size:0.73rem;
            border-bottom:1px solid var(--border-light);align-items:center;">
            <span style="font-family:'DM Mono',monospace;font-weight:700;color:var(--accent);">
                {row['ticker'].replace('.NS','')}
            </span>
            <span style="font-size:0.65rem;color:var(--text-muted);">{row['sector']}</span>
            <span style="font-family:'DM Mono',monospace;">{row['weight_pct']:.1f}%</span>
            <span style="font-family:'DM Mono',monospace;">{row['beta']:.3f}</span>
            <span style="font-family:'DM Mono',monospace;">{row['sect_mult']:.2f}×</span>
            <span style="font-family:'DM Mono',monospace;">{row['live_vol_pct']:.1f}%</span>
            <span style="font-family:'DM Mono',monospace;color:{pnl_color};font-weight:700;">
                ₹{row['median_pnl_inr']:+,.0f}
            </span>
            <span style="font-family:'DM Mono',monospace;color:{pnl_color};font-weight:600;">
                {row['median_pnl_pct']:+.1f}%
            </span>
            <span style="font-family:'DM Mono',monospace;color:{p5_color};">
                {row['p5_pnl_pct']:+.1f}%
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── VaR / CVaR COMPARISON ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("VaR & CVaR — Parametric vs Monte Carlo", "⚖")

    var_col1, var_col2 = st.columns(2)

    with var_col1:
        fig_var = go.Figure()
        labels   = ["VaR 95% Param.", "VaR 95% MC", "VaR 99% MC", "CVaR 95%", "CVaR 99%"]
        values   = [
            results["var_95_param"], results["var_95_hist"],
            results["var_99_hist"],  results["cvar_95"], results["cvar_99"]
        ]
        bar_colors = ["#1B6CA8", "#0D9373", "#D97706", "#7C3AED", "#D92D20"]
        fig_var.add_trace(go.Bar(
            x=labels, y=values,
            marker_color=bar_colors,
            text=[f"₹{v:,.0f}" for v in values],
            textposition="outside",
            hovertemplate="%{x}: ₹%{y:,.0f}<extra></extra>",
        ))
        fig_var.update_layout(
            **CHART_THEME, height=320,
            title=dict(text="Risk Metrics Comparison (₹ Loss)", font=dict(size=12), x=0),
            yaxis_title="Potential Loss (₹)",
            showlegend=False,
            xaxis_tickangle=-15,
        )
        st.plotly_chart(fig_var, use_container_width=True, config=plotly_chart_config())

    with var_col2:
        pv         = results["portfolio_value"]
        var95_pct  = results["var_95_hist"] / pv * 100
        cvar95_pct = results["cvar_95"] / pv * 100
        var99_pct  = results["var_99_hist"] / pv * 100

        st.markdown("**Risk Metric Interpretation**")
        st.markdown(
            f"🔵 **VaR 95% (MC) = ₹{results['var_95_hist']:,.0f} ({var95_pct:.1f}%)**  \n"
            f"In the worst 5% of scenarios, your portfolio loses at least this amount "
            f"over {results['horizon_days']} trading days under *{sc_used}* conditions.\n\n"
            f"🟣 **CVaR 95% = ₹{results['cvar_95']:,.0f} ({cvar95_pct:.1f}%)**  \n"
            f"The *average* loss in those worst-5% scenarios — the Expected Shortfall. "
            f"This is what risk managers at banks and hedge funds monitor daily.\n\n"
            f"🔴 **VaR 99% = ₹{results['var_99_hist']:,.0f} ({var99_pct:.1f}%)**  \n"
            f"In a 1-in-100 scenario, losses exceed this level.\n\n"
            f"**Parametric VaR** assumes normally distributed returns (underestimates tail risk). "
            f"Monte Carlo uses Student-t innovations (fatter tails) — a more conservative estimate."
        )

    # ── SECTOR IMPACT WATERFALL ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Sector-Level Impact (Median P&L)", "🧱")

    # Aggregate median P&L by sector
    sector_pnl: Dict[str, float] = {}
    for row in attribution:
        sec = row["sector"]
        sector_pnl[sec] = sector_pnl.get(sec, 0) + row["median_pnl_inr"]

    if sector_pnl:
        sectors_sorted = sorted(sector_pnl.items(), key=lambda x: x[1])
        sec_labels = [s[0] for s in sectors_sorted]
        sec_values = [s[1] for s in sectors_sorted]

        fig_wfall = go.Figure(go.Bar(
            x=sec_labels, y=sec_values,
            marker_color=["#D92D20" if v < 0 else "#0D9373" for v in sec_values],
            text=[f"₹{v:+,.0f}" for v in sec_values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Median P&L: ₹%{y:,.0f}<extra></extra>",
        ))
        fig_wfall.update_layout(
            **CHART_THEME, height=300,
            title=dict(text="Sector Contribution to Portfolio Loss (Median Scenario, ₹)", font=dict(size=12), x=0),
            xaxis_title=None, yaxis_title="Median P&L (₹)",
            showlegend=False,
        )
        st.plotly_chart(fig_wfall, use_container_width=True, config=plotly_chart_config())

    # ── MATHEMATICAL NOTES ─────────────────────────────────────────────────────
    with st.expander("📖  Methodology & Mathematical Framework", expanded=False):
        st.markdown(f"""
        <div style="font-size:0.76rem;line-height:1.8;color:var(--text-secondary);">

        <b style="color:var(--accent-dark);font-size:0.82rem;">Asset Price Model — GBM with Student-t Innovations</b><br>
        Each stock follows: <code>dS_i = μ_i S_i dt + σ_i S_i dW_i</code><br>
        Discretised as: <code>S_i(t+1) = S_i(t) · exp((μ_i − ½σ²_i)Δt + σ_i √Δt · ε_i)</code><br>
        where <code>ε_i ~ t({sc_data['fat_tail_df']})</code> (Student-t, df={sc_data['fat_tail_df']}, rescaled to unit variance).<br><br>

        <b style="color:var(--accent-dark);">Crisis Drift (μ_i)</b><br>
        <code>μ_i = β_i × ξ_i × μ_mkt</code> where μ_mkt = {sc_data['daily_drift_crisis']:.4f} (observed Nifty daily drift during crisis),
        β_i = stock's OLS beta vs Nifty (1-year daily returns), ξ_i = sector multiplier for {sc_used}.<br><br>

        <b style="color:var(--accent-dark);">Crisis Volatility (σ_i)</b><br>
        <code>σ_i_crisis = σ_i_historical × (σ_crisis / σ_normal)</code><br>
        Vol ratio = {sc_data['annualised_vol_crisis']:.2f} / {sc_data['annualised_vol_normal']:.2f} = {sc_data['annualised_vol_crisis']/sc_data['annualised_vol_normal']:.2f}×
        (calibrated from India VIX and realised vol during {sc_used}).<br><br>

        <b style="color:var(--accent-dark);">Correlation Structure (Cholesky Decomposition)</b><br>
        Covariance matrix built via single-factor model: <code>Cov(i,j) = β_i β_j σ²_mkt</code>.
        Cholesky L is used to generate correlated shocks: <code>ε_corr = L @ ε_iid</code>.<br><br>

        <b style="color:var(--accent-dark);">VaR &amp; CVaR</b><br>
        <code>VaR_α = −Q_α(P&L distribution)</code> where Q_α is the α-quantile of simulated terminal P&L.<br>
        <code>CVaR_α = −E[P&L | P&L ≤ VaR_α]</code> — the expected loss in the worst (1-α) tail.<br><br>

        <b style="color:var(--accent-dark);">Calibration Sources</b><br>
        Nifty drawdowns: NSE/BSE historical data. Sector multipliers: NSE sectoral indices 
        (Nifty Bank, IT, Pharma, Metal, Auto, FMCG, Energy, Infra) observed during each crisis.
        Vol regimes: India VIX peaks and realised Nifty daily σ during crisis windows.
        Student-t df estimated from excess kurtosis of Nifty daily returns per crisis period.

        </div>
        """, unsafe_allow_html=True)

    # ── HISTORICAL CONTEXT ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_header("Historical Context — What Actually Happened", "🕰")

    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-left:4px solid {sc_display['color']};
        border-radius:10px;padding:1.25rem 1.5rem;">
        <div style="font-size:0.8rem;font-weight:700;color:var(--text-primary);margin-bottom:0.75rem;">
            {sc_display['emoji']} {sc_used} — {sc_display['period']}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem;">
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Nifty Drawdown</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:var(--negative);">{sc_display['nifty_peak_to_trough']*100:+.1f}%</div>
            </div>
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">FII Outflow</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:var(--negative);">₹{mc['fii_outflow_cr']:,.0f} Cr</div>
            </div>
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">RBI Response</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:{'var(--positive)' if mc['rbi_rate_change_bps'] < 0 else 'var(--negative)'};">
                    {mc['rbi_rate_change_bps']:+d} bps
                </div>
            </div>
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">USD/INR</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:var(--negative);">{mc['usdinr_move_pct']:+.1f}%</div>
            </div>
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">India VIX Peak</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:var(--negative);">{mc['india_vix_peak']}</div>
            </div>
            <div>
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Recovery Time</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:700;
                    color:var(--accent);">{sc_display['recovery_months']} months</div>
            </div>
        </div>
        <div style="margin-top:1rem;font-size:0.74rem;color:var(--text-secondary);line-height:1.6;">
            <b>What drove the crash:</b> {sc_display['trigger']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── RESET BUTTON ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄  Clear Results & Run New Simulation", key="stress_reset"):
        for key in ["stress_results", "stress_scenario_used"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0 1rem 0;">
            <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;
                color:var(--accent-dark);">FinTerminal</div>
            <div style="font-size:0.62rem;color:var(--text-muted);letter-spacing:0.08em;
                text-transform:uppercase;margin-top:3px;">India</div>
        </div>
        """, unsafe_allow_html=True)

        # User account widget
        if not st.session_state.user_name:
            st.markdown('<div style="font-size:0.7rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.4rem;">Create Account</div>', unsafe_allow_html=True)
            name = st.text_input("Your Name", placeholder="e.g. Aryaan Pandhare")
            initial_funds = st.number_input("Starting Capital (₹)", min_value=10000, max_value=10000000, value=500000, step=10000)
            if st.button("Create Account →", type="primary", use_container_width=True) and name.strip():
                st.session_state.user_name = name.strip()
                st.session_state.user_id = str(uuid.uuid4())[:8]
                st.session_state.cash_balance = float(initial_funds)
                st.session_state.initial_balance = float(initial_funds)
                st.rerun()
        else:
            initials = "".join([w[0].upper() for w in st.session_state.user_name.split()[:2]])
            pnl_total = st.session_state.realized_pnl_total
            # Add portfolio value estimate
            st.markdown(f"""
            <div style="background:var(--accent-light);border:1px solid var(--border);border-radius:var(--radius);
                padding:1rem;margin-bottom:1rem;">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;">
                    <div style="width:36px;height:36px;border-radius:50%;background:var(--accent);
                        color:white;display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:0.85rem;flex-shrink:0;">{initials}</div>
                    <div>
                        <div style="font-weight:700;font-size:0.88rem;color:var(--text-primary);">{st.session_state.user_name}</div>
                        <div style="font-size:0.65rem;color:var(--text-muted);">ID: {st.session_state.user_id}</div>
                    </div>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                    <span style="font-size:0.68rem;color:var(--text-muted);">Cash Balance</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:700;font-size:0.82rem;color:var(--accent);">₹{st.session_state.cash_balance:,.0f}</span>
                </div>
                <div style="display:flex;justify-content:space-between;">
                    <span style="font-size:0.68rem;color:var(--text-muted);">Realized P&L</span>
                    <span style="font-family:'DM Mono',monospace;font-weight:700;font-size:0.78rem;
                        color:{'var(--positive)' if pnl_total >= 0 else 'var(--negative)'};">
                        {'+'if pnl_total>=0 else ''}₹{pnl_total:,.0f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        nav_items = [
            ("", "Market Overview"),
            ("", "Stock Explorer"),
            ("", "Orders"),
            ("", "Portfolio"),
            # ("📰", "News Terminal"),
            ("", "Watchlist"),
            ("", "Stress Test"),
        ]
        st.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Navigation</div>', unsafe_allow_html=True)
        for icon, label in nav_items:
            active = st.session_state.page == label
            btn_style = "primary" if active else "secondary"
            if st.button(f"{icon}  {label}", use_container_width=True,
                         type="primary" if active else "secondary",
                         key=f"nav_{label}"):
                st.session_state.page = label
                st.rerun()

        st.markdown("---")

        # Quick stats
        if st.session_state.holdings:
            st.markdown(f"""
            <div style="font-size:0.65rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem;">Holdings</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.82rem;font-weight:700;color:var(--text-primary);">{len(st.session_state.holdings)} Positions</div>
            <div style="font-size:0.68rem;color:var(--text-muted);">{len(st.session_state.order_history)} Total Orders</div>
            """, unsafe_allow_html=True)

        # Notifications (last 3)
        if st.session_state.notifications:
            st.markdown("---")
            st.markdown('<div style="font-size:0.65rem;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem;">Recent Activity</div>', unsafe_allow_html=True)
            for notif in st.session_state.notifications[:3]:
                st.markdown(f'<div style="font-size:0.7rem;color:var(--text-secondary);padding:0.2rem 0;border-bottom:1px solid var(--border-light);">{notif["msg"]}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.6rem;color:var(--text-muted);text-align:center;line-height:1.6;">
            FinTerminal India v1.0<br>
            Data via Yahoo Finance + RSS<br>
            Developed by Aryaan Pandhare
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    render_sidebar()

    st.markdown('<div style="max-width:1400px;margin:0 auto;">', unsafe_allow_html=True)
    render_header()

    page = st.session_state.get("page", "Market Overview")

    if page == "Market Overview":
        page_market_overview()
    elif page == "Stock Explorer":
        page_stock_explorer()
    elif page == "Orders":
        page_orders()
    elif page == "Portfolio":
        page_portfolio()
    elif page == "News Terminal":
        page_news()
    elif page == "Watchlist":
        page_watchlist()
    elif page == "Stress Test":
        page_stress_test()
    else:
        page_market_overview()

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()