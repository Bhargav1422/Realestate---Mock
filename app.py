
#!/usr/bin/env python3
# app.py — Prasad Realty (Streamlit Cloud–ready, hardened + validation)
# - Clean HTML/CSS (no escapes), consistent buttons (nowrap), scrollable JSON
# - Validation for login, contact form, and site-visit dialog (name/phone/email/message)
# - Fallbacks for Streamlit versions (dialog/link_button), cached data loading (conditional)
# - Robust paths and error handling; defensive UI guards

import base64
import json
import os
import re
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

import pandas as pd
import pydeck as pdk
import streamlit as st

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
.card, .brand-card {
  border-radius: 14px; background: rgba(17,24,39,0.72); border: 1px solid var(--border);
}
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

/* Sticky filter container */
.filters {
  position: sticky; top: 64px; z-index: 5; backdrop-filter: blur(6px);
  display:grid; grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px; padding: 12px 16px;
}
.filters .stSelectbox, .filters .stSlider, .filters .stTextInput { min-height: 52px; }

.search-wrap { padding: 8px 16px 0 16px; }
img { border-radius: 12px; }

/* Scrollable JSON box for Details to avoid layout blowouts */
.json-box {
  max-height: 340px;
  overflow: auto;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(17,24,39,0.55);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------
# Branding / constants
# --------------------------------------------------
PRASAD_IG_HANDLE = "prasad.realty_vizag"
PRASAD_IG_URL = "https://www.instagram.com/prasad.realty_vizag?igsh=MWc3ZjN6dWwxNDNkZw=="
PRASAD_PHONE = "+916309729493"
PRASAD_WHATSAPP = "https://wa.me/916309729493"
PRASAD_LOGO_PATH = "assets/prasad_logo.png"

# --------------------------------------------------
# Validators (basic, safe)
# --------------------------------------------------
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{8,15}$")  # digits +/- separators, 9–16 chars total
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    name = (name or "").strip()
    if not name:
        return False, "Name is required."
    if len(name) < 2:
        return False, "Name must be at least 2 characters."
    return True, None


def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    phone = (phone or "").strip()
    if not phone:
        return False, "Phone is required (or provide an email)."
    if not PHONE_RE.match(phone):
        return False, "Enter a valid phone (digits, optional +, spaces/()- allowed)."
    return True, None


def validate_email(email: str, allow_blank: bool = True) -> Tuple[bool, Optional[str]]:
    email = (email or "").strip()
    if allow_blank and not email:
        return True, None
    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address."
    return True, None


def validate_message(msg: str) -> Tuple[bool, Optional[str]]:
    msg = (msg or "").strip()
    if not msg:
        return False, "Message cannot be empty."
    if len(msg) < 5:
        return False, "Message must be at least 5 characters."
    return True, None


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
        return (
            f"<img class='brand-logo' src='data:image/png;base64,{b64}' "
            f"width='{size}' height='{size}' alt='Prasadt feedback, fallback to success if toast not available."""
    try:
        st.toast(msg)
    except Exception:
        st.success(msg)


def safe_link_button(label: str, url: str, help: Optional[str] = None, key: Optional[str] = None):
    """Use st.link_button if available, else a styled <a role="button">."""
    if hasattr(st, "link_button"):
        try:
            st.link_button(label, url=url, key=key)
            return
        except TypeError:
            pass
        except Exception:
            pass
    html = (
        f"<a role='button' class='button-primary' href='{url}' target='_blank' "
        f"-------------------------------------------
# Session defaults
# --------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "leads" not in st.session_state:
    st.session_state.leads = []
if "favorites" not in st.session_state:
    st.session_state.favorites = set()
if "visit_fallback_open" not in st.session_state:
    st.session_state.visit_fallback_open = False
if "visit_fallback_p" not in st.session_state:
    st.session_state.visit_fallback_p = None


def _init_filters():
    defaults = {
        "s_region": "All",
        "s_condition": "All",
        "s_type": "All",
        "s_min_bed": 0,
        "s_budget": (0, 10_000_000),
        "s_sort": "Newest",
        "s_search": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_filters()

# --------------------------------------------------
# Sidebar (brand + login with validation)
# --------------------------------------------------
with st.sidebar:
    st.title("Prasad Realty")
    st.caption("Visakhapatnam · Residential & Plots")

    ig_link_html = (
        f"<a href='{PRASAD_IG_URL}' target='_blank' rel='noopener'  """
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
            ig_link=ig_link_html,
            phone=PRASAD_PHONE,
        ),
        unsafe_allow_html=True,
    )

    if st.session_state.user:
        st.success("Signed in as {u}".format(u=st.session_state.user))
        if st.button("Sign out", key="signout"):
            st.session_state.user = None
            st.rerun()
    else:
        name = st.text_input("Your name")
        if st.button("Continue", key="login"):
            ok, err = validate_name(name)
            if ok:
                st.session_state.user = name.strip()
                st.rerun()
            else:
                st.error(err)

if not st.session_state.user:
    st.info("Please login from the left sidebar to continue.")
    st.stop()

# --------------------------------------------------
# Data — Cloud-safe loader with conditional caching
# --------------------------------------------------
def _read_json(path: Path) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


FALLBACK = [
    {
        "id": 7,
        "title": "Independent 4BHK with garden",
        "region_key": "Hanumanthawaka",
        "condition": "New",
        "home_type": "Individual",
        "bedrooms": 4,
        "bathrooms": 4,
        "area_sqft": 2400,
        "price_inr": 22500000,
        "address": "Colony Rd, Hanumanthawaka",
        "image": "https://picsum.photos/seed/hanuman3/800/500",
        "insta_url": "",
        "lat": 17.7549,
        "lng": 83.3204,
        "images": [
            "https://picsum.photos/seed/h3/800/500",
            "https://picsum.photos/seed/h4/800/500",
        ],
        "distances": {"Beach": "3.2 km", "School": "750 m", "Hospital": "1.1 km"},
    },
    {
        "id": 9,
        "title": "MVP 2BHK corner flat",
        "region_key": "MVP Colony",
        "condition": "New",
        "home_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "area_sqft": 1050,
        "price_inr": 7800000,
        "address": "Sector 5, MVP Colony",
        "image": "https://picsum.photos/seed/mvp1/800/500",
        "insta_url": "",
        "lat": 17.7487,
        "lng": 83.3369,
        "images": [
            "https://picsum.photos/seed/m1/800/500",
            "https://picsum.photos/seed/m2/800/500",
        ],
    },
    {
        "id": 1,
        "title": "2BHK near park",
        "region_key": "Visalakshinagar",
        "condition": "New",
        "home_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "area_sqft": 980,
        "price_inr": 6500000,
        "address": "Plot 23, Visalakshinagar",
        "image": "https://picsum.photos/seed/visalakshi1/800/500",
        "insta_url": "",
        "lat": 17.7480,
        "lng": 83.3575,
        "images": [
            "https://picsum.photos/seed/v1/800/500",
            "https://picsum.photos/seed/v2/800/500",
        ],
    },
    {
        "id": 4,
        "title": "Luxury 4BHK penthouse",
        "region_key": "MVP Colony",
        "condition": "New",
        "home_type": "Apartment",
        "bedrooms": 4,
        "bathrooms": 4,
        "area_sqft": 2200,
        "price_inr": 32000000,
        "address": "Sector 1, MVP Colony",
        "image": "https://picsum.photos/seed/mvp4/800/500",
        "insta_url": "",
        "lat": 17.7387,
        "lng": 83.3277,
        "images": [
            "https://picsum.photos/seed/m4/800/500",
            "https://picsum.photos/seed/m5/800/500",
        ],
    },
]

if hasattr(st, "cache_data"):

    @st.cache_data(show_spinner=False)
    def load_data() -> List[Dict]:
        candidate_paths = [
            Path.cwd() / "properties.json",
            Path(__file__).parent / "properties.json"
            if "__file__" in globals()
            else Path.cwd() / "properties.json",
        ]
        for p in candidate_paths:
            if p.exists():
                data = _read_json(p)
                if isinstance(data, list) and data:
                    return data
        return FALLBACK

else:

    def load_data() -> List[Dict]:
        candidate_paths = [
            Path.cwd() / "properties.json",
            Path(__file__).parent / "properties.json"
            if "__file__" in globals()
            else Path.cwd() / "properties.json",
        ]
        for p in candidate_paths:
            if p.exists():
                data = _read_json(p)
                if isinstance(data, list) and data:
                    return data
        return FALLBACK


with st.spinner("Loading properties..."):
    data = load_data()

regions = sorted({p.get("region_key", "") for p in data if p.get("region_key")})
prices = [p.get("price_inr", 0) for p in data]
pmin_data = int(min(prices) if prices else 0)
pmax_data = int(max(prices) if prices else 10_000_000)

# --------------------------------------------------
# Filters UI (sticky) + search + chips
# --------------------------------------------------
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

st.markdown("<div class='filters'>", unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    region_options = ["All"] + regions
    try:
        region_index = region_options.index(st.session_state.s_region)
    except ValueError:
        region_index = 0
    st.session_state.s_region = st.selectbox("Region", region_options, index=region_index)
with c2:
    st.session_state.s_condition = st.selectbox(
        "Condition", ["All", "New", "Old"], index=["All", "New", "Old"].index(st.session_state.s_condition)
    )
with c3:
    st.session_state.s_type = st.selectbox(
        "Type", ["All", "Individual", "Apartment"], index=["All", "Individual", "Apartment"].index(st.session_state.s_type)
    )
with c4:
    beds_opts = [0, 1, 2, 3, 4, 5]
    idx = beds_opts.index(st.session_state.s_min_bed) if st.session_state.s_min_bed in beds_opts else 0
    st.session_state.s_min_bed = st.selectbox("Min bedrooms", beds_opts, index=idx)
with c5:
    min_v, max_v = st.session_state.s_budget
    min_v = max(pmin_data, int(min_v))
    max_v = min(pmax_data, int(max_v))
    if min_v > max_v:
        min_v, max_v = pmin_data, pmax_data
    st.session_state.s_budget = st.slider(
        "Budget (₹)", min_value=pmin_data, max_value=pmax_data, value=(min_v, max_v), step=500_000
    )
with c6:
    sort_opts = ["Newest", "Price ↑", "Price ↓", "Area ↑", "Area ↓"]
    st.session_state.s_sort = st.selectbox("Sort", sort_opts, index=sort_opts.index(st.session_state.s_sort))
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='search-wrap'>", unsafe_allow_html=True)
st.session_state.s_search = st.text_input("Search (title/address)", value=st.session_state.s_search)
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# Filter + sort functions
# --------------------------------------------------
def matches(p: Dict) -> bool:
    s = st.session_state
    if s.s_region != "All" and p.get("region_key") != s.s_region:
        return False
    if s.s_condition != "All" and p.get("condition") != s.s_condition:
        return False
    if s.s_type != "All" and p.get("home_type") != s.s_type:
        return False
    if s.s_min_bed and int(p.get("bedrooms", 0)) < int(s.s_min_bed):
        return False
    bmin, bmax = s.s_budget
    price = int(p.get("price_inr", 0))
    if not (int(bmin) <= price <= int(bmax)):
        return False
    qlc = (s.s_search or "").lower().strip()
    if qlc:
        hay = (p.get("title", "") + " " + p.get("address", "")).lower()
        if qlc not in hay:
            return False
    return True


def sorter_key(p: Dict):
    s = st.session_state
    if s.s_sort == "Price ↑":
        return p.get("price_inr", 0)
    if s.s_sort == "Price ↓":
        return -p.get("price_inr", 0)
    if s.s_sort == "Area ↑":
        return p.get("area_sqft", 0)
    if s.s_sort == "Area ↓":
        return -p.get("area_sqft", 0)
    return -p.get("id", 0)  # Newest (by id desc)


filtered = sorted([p for p in data if matches(p)], key=sorter_key)

# --------------------------------------------------
# Dialog helper (with validation) + fallbacks
# --------------------------------------------------
def save_visit_lead(
    p: Dict, name: str, phone: str, email: str, visit_date: date, visit_time: time, note: str
) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    ok_name, err_name = validate_name(name)
    if not ok_name:
        errors.append(err_name)

    phone_clean = (phone or "").strip()
    email_clean = (email or "").strip()
    if not phone_clean and not email_clean:
        errors.append("Provide at least one contact method: phone or email.")
    else:
        if phone_clean:
            ok_ph, err_ph = validate_phone(phone_clean)
            if not ok_ph:
                errors.append(err_ph)
        if email_clean:
            ok_em, err_em = validate_email(email_clean, allow_blank=False)
            if not ok_em:
                errors.append(err_em)

    if not isinstance(visit_date, date):
        errors.append("Please select a valid date.")
    if not isinstance(visit_time, time):
        errors.append("Please select a valid time.")

    if errors:
        return False, errors

    lead = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "property_id": p.get("id"),
        "title": p.get("title"),
        "region": p.get("region_key"),
        "name": name.strip(),
        "phone": phone_clean,
        "email": email_clean,
        "visit_date": str(visit_date),
        "visit_time": str(visit_time),
        "note": (note or "").strip(),
        "source": "site_visit",
    }
    st.session_state.leads.append(lead)
    return True, []


def open_visit_dialog(p: Dict):
    """Open a Streamlit dialog if available; else fallback to a page section."""
    if hasattr(st, "dialog"):
        @st.dialog("Book a site visit", width="large")
        def _dlg():
            st.markdown("**{t}** · {r}".format(t=p.get("title", ""), r=p.get("region_key", "")))
            visit_date = st.date_input("Date", key="dlg_date_{id}".format(id=p.get("id", "x")))
            visit_time = st.time_input("Time", value=time(11, 30), key="dlg_time_{id}".format(id=p.get("id", "x")))
            name = st.text_input("Your name", key="dlg_nm_{id}".format(id=p.get("id", "x")))
            phone = st.text_input("Phone", key="dlg_ph_{id}".format(id=p.get("id", "x")))
            email = st.text_input("Email", key="dlg_em_{id}".format(id=p.get("id", "x")))
            note = st.text_area("Note", key="dlg_nt_{id}".format(id=p.get("id", "x")))

            if st.button("Request visit", key="dlg_req_{id}".format(id=p.get("id", "x"))):
                ok, errs = save_visit_lead(p, name, phone, email, visit_date, visit_time, note)
                if ok:
                    toast_ok("Visit requested. We'll contact you soon.")
                    st.rerun()
                else:
                    for e in errs:
                        st.error(e)

        _dlg()
    elif hasattr(st, "experimental_dialog"):
        @st.experimental_dialog("Book a site visit")
        def _dlg():
            st.markdown("**{t}** · {r}".format(t=p.get("title", ""), r=p.get("region_key", "")))
            visit_date = st.date_input("Date", key="xdlg_date_{id}".format(id=p.get("id", "x")))
            visit_time = st.time_input("Time", value=time(11, 30), key="xdlg_time_{id}".format(id=p.get("id", "x")))
            name = st.text_input("Your name", key="xdlg_nm_{id}".format(id=p.get("id", "x")))
            phone = st.text_input("Phone", key="xdlg_ph_{id}".format(id=p.get("id", "x")))
            email = st.text_input("Email", key="xdlg_em_{id}".format(id=p.get("id", "x")))
            note = st.text_area("Note", key="xdlg_nt_{id}".format(id=p.get("id", "x")))

            if st.button("Request visit", key="xdlg_req_{id}".format(id=p.get("id", "x"))):
                ok, errs = save_visit_lead(p, name, phone, email, visit_date, visit_time, note)
                if ok:
                    toast_ok("Visit requested. We'll contact you soon.")
                    st.rerun()
                else:
                    for e in errs:
                        st.error(e)

        _dlg()
    else:
        st.session_state.visit_fallback_p = p
        st.session_state.visit_fallback_open = True


# --------------------------------------------------
# Listings + Map (Hero removed per request; buttons per property)
# --------------------------------------------------
st.markdown("## Listings")

if not filtered:
    st.warning("No properties match your filters.")
else:
    map_df = pd.DataFrame(
        [
            {
                "lat": p.get("lat"),
                "lon": p.get("lng"),
                "title": p.get("title", ""),
                "price": p.get("price_inr", 0),
            }
            for p in filtered
            if p.get("lat") and p.get("lng")
        ]
    )
    if not map_df.empty:
        st.markdown("### Map view")
        try:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position="[lon, lat]",
                get_fill_color="[34, 211, 238, 160]",
                get_radius=60,
                pickable=True,
            )
            vs = pdk.ViewState(
                latitude=float(map_df.lat.mean()), longitude=float(map_df.lon.mean()), zoom=12
            )
            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=vs,
                    tooltip={"text": "{title} — ₹{price}"},
                )
            )
        except Exception:
            st.info("Map is unavailable at the moment.")

    cols = st.columns(3)
    for i, p in enumerate(filtered):
        with cols[i % 3]:
            st.markdown("<div class='property-card'>", unsafe_allow_html=True)

            st.image(p.get("image", ""), use_column_width=True)
            st.markdown("**{t}**".format(t=p.get("title", "")))
            st.markdown(
                "<span class='price'>₹{n:,.0f}</span>".format(n=float(p.get("price_inr", 0))),
                unsafe_allow_html=True,
            )
            st.markdown(
                "<span class='badge'>{rk}</span>"
                "<span class='badge'>{c}</span>"
                "<span class='badge'>{ht}</span>"
                "<span class='badge'>{br} BR</span>"
                "<span class='badge'>{sf} sqft</span>".format(
                    rk=p.get("region_key", ""),
                    c=p.get("condition", ""),
                    ht=p.get("home_type", ""),
                    br=p.get("bedrooms", 0),
                    sf=p.get("area_sqft", 0),
                ),
                unsafe_allow_html=True,
            )
            dists = p.get("distances", {})
            if dists:
                st.markdown(
                    " ".join(
                        [
                            "<span class='badge'>{k}: {v}</span>".format(k=k, v=v)
                            for k, v in dists.items()
                        ]
                    ),
                    unsafe_allow_html=True,
                )
            st.caption(p.get("address", ""))

            pics = [p.get("image", "")] + p.get("images", [])
            pics = [x for x in pics if x]
            if pics:
                sel = st.selectbox(
                    "Gallery",
                    options=range(len(pics)),
                    format_func=lambda idx: "Photo {n}".format(n=idx + 1),
                    key="gal_{id}".format(id=p.get("id", i)),
                )
                st.image(pics[sel], use_column_width=True)

            b1, b2, b3, b4 = st.columns(4)
            st.markdown("<div class='property-cta'>", unsafe_allow_html=True)
            with b1:
                insta = p.get("insta_url", "")
                if insta:
                    safe_link_button(
                        "Instagram",
                        url=insta,
                        key="insta_{id}".format(id=p.get("id", i)),
                    )
                else:
                    st.button(
                        "Instagram", key="insta_disabled_{id}".format(id=p.get("id", i)), disabled=True
                    )
            with b2:
                txt = quote_plus(
                    "Hi Prasad Realty, I'm interested in '{t}' in {r}.".format(
                        t=p.get("title", ""), r=p.get("region_key", "")
                    )
                )
                utm = "utm_source=streamlit&utm_medium=cta&utm_campaign=prasad_demo"
                safe_link_button(
                    "WhatsApp",
                    url="{wa}?text={txt}&{utm}".format(wa=PRASAD_WHATSAPP, txt=txt, utm=utm),
                    key="wa_{id}".format(id=p.get("id", i)),
                )
            with b3:
                pid = p.get("id", i)
                fav_key = "fav_{id}".format(id=pid)
                is_fav = pid in st.session_state.favorites
                if st.button(("💙 Unfavorite" if is_fav else "❤️ Favorite"), key=fav_key):
                    if is_fav:
                        st.session_state.favorites.remove(pid)
                        toast_ok("Removed from favorites")
                    else:
                        st.session_state.favorites.add(pid)
                        toast_ok("Added to favorites")
            with b4:
                pid = p.get("id", i)
                if st.button("Details", key="d_{id}".format(id=pid)):
                    st.session_state["show_{id}".format(id=pid)] = not st.session_state.get(
                        "show_{id}".format(id=pid), False
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            pid = p.get("id", i)
            if st.session_state.get("show_{id}".format(id=pid), False):
                with st.expander("Details", expanded=True):
                    st.markdown("<div class='json-box'>", unsafe_allow_html=True)
                    st.json({k: v for k, v in p.items() if k != "image"})
                    st.markdown("</div>", unsafe_allow_html=True)

                    st.markdown("**EMI Calculator**")
                    emi1, emi2, emi3 = st.columns(3)
                    with emi1:
                        loan_amt = st.number_input(
                            "Loan amount (₹)",
                            value=float(p.get("price_inr", 0)),
                            min_value=0.0,
                            step=100000.0,
                            key="loan_{id}".format(id=pid),
                        )
                    with emi2:
                        rate = st.number_input(
                            "Interest (% p.a.)",
                            value=8.5,
                            min_value=0.0,
                            step=0.1,
                            key="rate_{id}".format(id=pid),
                        )
                    with emi3:
                        years = st.number_input(
                            "Tenure (years)", value=20, min_value=1, step=1, key="years_{id}".format(id=pid)
                        )
                    r = (rate / 100.0) / 12.0
                    n = int(years * 12)
                    if n > 0:
                        emi = (loan_amt / n) if r == 0 else loan_amt * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
                    else:
                        emi = 0.0
                    st.write("**Estimated EMI:** ₹{m:,.0f} / month".format(m=emi))

                    if st.button("Book visit", key="bk_{id}".format(id=pid)):
                        open_visit_dialog(p)

            st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# Fallback visit section (if dialog API not available) — with validation
# --------------------------------------------------
if st.session_state.visit_fallback_open and st.session_state.visit_fallback_p:
    p = st.session_state.visit_fallback_p
    st.markdown("### Book a site visit (fallback)")
    st.markdown("**{t}** · {r}".format(t=p.get("title", ""), r=p.get("region_key", "")))
    visit_date = st.date_input("Date", key="fb_date_{id}".format(id=p.get("id", "x")))
    visit_time = st.time_input("Time", value=time(11, 30), key="fb_time_{id}".format(id=p.get("id", "x")))
    name = st.text_input("Your name", key="fb_nm_{id}".format(id=p.get("id", "x")))
    phone = st.text_input("Phone", key="fb_ph_{id}".format(id=p.get("id", "x")))
    email = st.text_input("Email", key="fb_em_{id}".format(id=p.get("id", "x")))
    note = st.text_area("Note", key="fb_nt_{id}".format(id=p.get("id", "x")))
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("Request visit", key="fb_req_{id}".format(id=p.get("id", "x"))):
            ok, errs = save_visit_lead(p, name, phone, email, visit_date, visit_time, note)
            if ok:
                toast_ok("Visit requested. We'll contact you soon.")
                st.session_state.visit_fallback_open = False
                st.session_state.visit_fallback_p = None
                st.rerun()
            else:
                for e in errs:
                    st.error(e)
    with cc2:
        if st.button("Cancel", key="fb_cancel"):
            st.session_state.visit_fallback_open = False
            st.session_state.visit_fallback_p = None
            st.rerun()

# --------------------------------------------------
# Quick contact + CSV — with validation
# --------------------------------------------------
st.markdown("---")
st.subheader("Quick contact")
qc1, qc2, qc3 = st.columns([2, 2, 3])
with qc1:
    qn = st.text_input("Your name", key="qc_name")
with qc2:
    qp = st.text_input("Phone", key="qc_phone")
with qc3:
    qe = st.text_input("Email", key="qc_email")
msg = st.text_area("Message", key="qc_msg")

cc1, cc2 = st.columns(2)
with cc1:
    if st.button("Send message", key="send_msg"):
        errs: List[str] = []
        ok_n, err_n = validate_name(qn)
        if not ok_n:
            errs.append(err_n)

        qp_clean = (qp or "").strip()
        qe_clean = (qe or "").strip()
        if not qp_clean and not qe_clean:
            errs.append("Provide at least one contact method: phone or email.")
        else:
            if qp_clean:
                ok_p, err_p = validate_phone(qp_clean)
                if not ok_p:
                    errs.append(err_p)
            if qe_clean:
                ok_e, err_e = validate_email(qe_clean, allow_blank=False)
                if not ok_e:
                    errs.append(err_e)

        ok_m, err_m = validate_message(msg)
        if not ok_m:
            errs.append(err_m)

        if errs:
            for e in errs:
                st.error(e)
        else:
            lead = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "property_id": None,
                "title": None,
                "region": None,
                "name": qn.strip(),
                "phone": qp_clean,
                "email": qe_clean,
                "visit_date": "",
                "visit_time": "",
                "note": (msg or "").strip(),
                "source": "contact_form",
            }
            st.session_state.leads.append(lead)
            toast_ok("Message saved (demo).")

with cc2:
    if st.session_state.leads:
        df = pd.DataFrame(st.session_state.leads)
        st.download_button(
            "Download leads (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="leads.csv",
            mime="text/csv",
        )
    else:
        st.button("Download leads (CSV)", key="dl_disabled", disabled=True)
