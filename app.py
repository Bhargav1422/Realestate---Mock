
# app.py — Prasad Realty (Streamlit prototype, simplified and alignment-fixed)
# Features:
# - Prasad Realty branding (Instagram deep link + circular logo)
# - Mobile-friendly layout and sticky filter bar
# - Favorites, toast feedback, site-visit dialog
# - Gallery (simple select), EMI calculator
# - Map pins (pydeck) if properties have lat/lng
# - Quick chips (demo shortcuts), lead CSV export
# - Duplicate-safe widget keys
# - No fragile f-strings in HTML; uses .format for all HTML blocks

import json
import os
import base64
from pathlib import Path
from datetime import datetime, time
from urllib.parse import quote_plus

import streamlit as st
import pandas as pd
import pydeck as pdk

# --------------------------------------------------
# Page / Theme
# --------------------------------------------------
st.set_page_config(page_title="Prasad Realty", page_icon="🏠", layout="wide")

CSS = """
<style>
:root {
  --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8;
  --accent:#22d3ee; --primary:#38bdf8; --border:#1f2937;
}
html, body, [class*="stApp"] {
  background: linear-gradient(135deg, #0b1020, var(--bg));
  color: var(--text);
}
.block-container { padding-top: 0.8rem; }

/* Cards */
.card, .hero, .brand-card {
  border-radius: 14px; background: rgba(17,24,39,0.72); border: 1px solid var(--border);
}
.hero { padding: 14px 16px; margin-bottom: 12px; }
.brand-card { padding: 12px; }

/* Hover affordance on property cards */
.property-card { transition: transform .18s ease, box-shadow .18s ease; }
.property-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.25); }

.badge {
  display:inline-block; margin-right:6px; margin-top:6px;
  padding:4px 8px; border-radius:999px; border:1px solid #334155; color: var(--muted); font-size:12px;
}
.price { font-weight:700; color: var(--accent); }
.button-primary {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color:#0b1220; border:0; padding:10px 14px; border-radius:10px; font-weight:600;
}

/* Circular brand logo */
.brand-card .brand-logo {
  border-radius: 50%;
  border: 2px solid var(--accent);
}

/* Layout helpers */
.flex { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.flex-wrap { flex-wrap:wrap; }

/* Filters: sticky bar + grid alignment */
.filters {
  position: sticky; top: 64px; z-index: 5; backdrop-filter: blur(6px);
  display:grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px; padding: 12px 16px;
}
.filters .stSelectbox, .filters .stSlider, .filters .stTextInput { min-height: 52px; }

/* Neutral spacing around slider to avoid label overlap across versions */
.filters div[data-testid="stSlider"] { padding-top: 4px; }

.search-wrap { padding: 8px 16px 0 16px; }
.property-caption { margin-top: 6px; }
.cta-row { margin-top: 8px; }
img { border-radius: 12px; }

/* Mobile sticky action bar — visible only on phones */
.mobile-bar {
  position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%);
  display: none; gap: 8px; padding: 8px 10px; border-radius: 999px;
  background: rgba(17,24,39,0.85); border: 1px solid var(--border); z-index: 10;
}
.mobile-bar a { text-decoration: none; }

/* Responsive filters */
@media (max-width: 900px) { .filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) {
  .filters { grid-template-columns: 1fr; }
  .hero { padding: 12px; }
  .mobile-bar { display: flex; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------
# Branding / constants — replace with your values
# --------------------------------------------------
PRASAD_IG_HANDLE = "prasad.realty_vizag"
PRASAD_IG_URL = "https://www.instagram.com/prasad.realty_vizag?igsh=MWc3ZjN6dWwxNDNkZw=="
PRASAD_PHONE = "+916309729493"
PRASAD_WHATSAPP = "https://wa.me/916309729493"
PRASAD_LOGO_PATH = "prasad_logo.png"  # put your logo PNG here

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def brand_logo_img(path: str, size: int = 64) -> str:
    """Return a circular <img> tag with base64-embedded logo; empty string if missing."""
    try:
        if not os.path.isfile(path):
            return ""
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return "<img class='brand-logo' src='data:image/png;base64,{b64}' width='{w}' height='{h}' alt except Exception:
        return ""

def toast_ok(msg: str):
    """Toast feedback (with success fallback)."""
    try:
        st.toast(msg)
    except Exception:
        st.success(msg)

# --------------------------------------------------
# Session defaults
# --------------------------------------------------
if "user" not in st.session_state: st.session_state.user = None
if "leads" not in st.session_state: st.session_state.leads = []
if "favorites" not in st.session_state: st.session_state.favorites = set()

# Filter state (kept simple, but lets chips alter slider)
def _init_filters():
    defaults = {
        "s_region": "All", "s_condition": "All", "s_type": "All",
        "s_min_bed": 0, "s_budget": (0, 10_000_000), "s_sort": "Newest", "s_search": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
_init_filters()

# --------------------------------------------------
# Sidebar (brand + login)
# --------------------------------------------------
with st.sidebar:
    st.title("Prasad Realty")
    st.caption("Visakhapatnam · Residential & Plots")

    # Brand card with circular logo + Instagram link
    ig_link = "<a href='{urla>".format(url=PRASAD_IG_URL)
    st.markdown(
        """
        <div class='brand-card'>
          <div class='flex'>
            <div style='display:flex;align-items:center;gap:10px;'>
              {logo}
              <div>
                <div style='font-weight:700;'>Prasad Realty</div>
                <div class='small'>Instagram: @{handle}</div>
              </div>
            </div>
            {ig_link}
          </div>
          <div style='margin-top:6px;' class='small'>Call / WhatsApp: {phone}</div>
        </div>
        """.format(
            logo=brand_logo_img(PRASAD_LOGO_PATH, size=64),
            handle=PRASAD_IG_HANDLE,
            ig_link=ig_link,
            phone=PRASAD_PHONE
        ),
        unsafe_allow_html=True
    )

    # Mock login
    if st.session_state.user:
        st.success("Signed in as {u}".format(u=st.session_state.user))
        if st.button("Sign out", key="signout"):
            st.session_state.user = None
            st.rerun()
    else:
        name = st.text_input("Your name")
        if st.button("Continue", key="login"):
            if name.strip():
                st.session_state.user = name.strip()
                st.rerun()
            else:
                st.error("Please enter a name")

if not st.session_state.user:
    st.info("Please login from the left sidebar to continue.")
    st.stop()

# --------------------------------------------------
# Data
# --------------------------------------------------
DATA_PATH = Path(__file__).parent / "properties.json"
FALLBACK = [
    {"id":7,"title":"Independent 4BHK with garden","region_key":"Hanumanthawaka","condition":"New","home_type":"Individual",
     "bedrooms":4,"bathrooms":4,"area_sqft":2400,"price_inr":22500000,"address":"Colony Rd, Hanumanthawaka",
     "image":"https://picsum.photos/seed/hanuman3/800/500","insta_url":"","lat":17.7549,"lng":83.3204,
     "images":["https://picsum.photos/seed/h3/800/500","https://picsum.photos/seed/h4/800/500"],
     "distances":{"Beach":"3.2 km","School":"750 m","Hospital":"1.1 km"}},
    {"id":9,"title":"MVP 2BHK corner flat","region_key":"MVP Colony","condition":"New","home_type":"Apartment",
     "bedrooms":2,"bathrooms":2,"area_sqft":1050,"price_inr":7800000,"address":"Sector 5, MVP Colony",
     "image":"https://picsum.photos/seed/mvp1/800/500","insta_url":"","lat":17.7487,"lng":83.3369,
     "images":["https://picsum.photos/seed/m1/800/500","https://picsum.photos/seed/m2/800/500"]},
    {"id":1,"title":"2BHK near park","region_key":"Visalakshinagar","condition":"New","home_type":"Apartment",
     "bedrooms":2,"bathrooms":2,"area_sqft":980,"price_inr":6500000,"address":"Plot 23, Visalakshinagar",
     "image":"https://picsum.photos/seed/visalakshi1/800/500","insta_url":"","lat":17.7480,"lng":83.3575,
     "images":["https://picsum.photos/seed/v1/800/500","https://picsum.photos/seed/v2/800/500"]},
    {"id":4,"title":"Luxury 4BHK penthouse","region_key":"MVP Colony","condition":"New","home_type":"Apartment",
     "bedrooms":4,"bathrooms":4,"area_sqft":2200,"price_inr":32000000,"address":"Sector 1, MVP Colony",
     "image":"https://picsum.photos/seed/mvp4/800/500","insta_url":"","lat":17.7387,"lng":83.3277,
     "images":["https://picsum.photos/seed/m4/800/500","https://picsum.photos/seed/m5/800/500"]}
]
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = FALLBACK

# Regions and price bounds
regions = sorted({p["region_key"] for p in data})
prices = [p.get("price_inr", 0) for p in data]
pmin_data = min(prices) if prices else 0
pmax_data = max(prices) if prices else 10_000_000

# --------------------------------------------------
# Hero + Mobile CTA bar
# --------------------------------------------------
wa_link = "<a href='{url}' target='_blank'RASAD_WHATSAPP)
ig_link_small = "{url}Instagram</a>".format(url=PRASAD_IG_URL)

st.markdown(
    """
    <div class='hero'>
      <div class='flex flex-wrap'>
        <div>
          <div style='font-weight:800;font-size:20px;'>Find your home in Vizag</div>
          <div class='small'>Filter by area, price, and type. Book a site visit in one click.</div>
        </div>
        {wa_link}
      </div>
    </div>
    """.format(wa_link=wa_link),
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='mobile-bar'>
      {wa_link}
      {ig_link}
    </div>
    """.format(wa_link=wa_link, ig_link=ig_link_small),
    unsafe_allow_html=True
)

# --------------------------------------------------
# Filters UI (sticky) + search + chips
# --------------------------------------------------
# Quick chips (demo shortcuts)
ch1, ch2, ch3, ch4 = st.columns(4)
with ch1:
    if st.button("₹50–80L", key="chip_5080"):
        st.session_state.s_budget = (5_000_000, 8_000_000)
        toast_ok("Applied ₹50–80L budget")
with ch2:
    if st.button("Sea-facing", key="chip_sea"):
        toast_ok("Demo chip: add 'sea-facing' tag to properties.json to use")
with ch3:
    if st.button("Gated community", key="chip_gated"):
        toast_ok("Demo chip: add 'amenities': ['Gated'] to properties.json to use")
with ch4:
    st.caption("Favorites: {n}".format(n=len(st.session_state.favorites)))

# Sticky filter bar (single grid ensures alignment)
st.markdown("<div class='filters'>", unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
