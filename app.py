
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
PRASAD_LOGO_PATH = "assets/prasad_logo.png"  # put your logo PNG here

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
    return "<img class='brand-logo' src".format(
      b64=b64, w=size, h=size
    )
  except Exception:
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
        {ig}Follow</a>
      </div>
      <div style='margin-top:6px;' class='small'>Call / WhatsApp: {phone}</div>
    </div>
    """.format(
      logo=brand_logo_img(PRASAD_LOGO_PATH, size=64),
      handle=PRASAD_IG_HANDLE,
      ig=PRASAD_IG_URL,
      phone=PRASAD_PHONE
    ),
    unsafe_allow_html=True
  )

  # Mock login
  if st.session_state.user:
    st.success(f"Signed in as {st.session_state.user}")
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
st.markdown(
  """
  <div class='hero'>
    <div class='flex flex-wrap'>
      <div>
        <div style='font-weight:800;font-size:20px;'>Find your home in Vizag</div>
        <div class='small'>Filter by area, price, and type. Book a site visit in one click.</div>
      </div>
      {wa}WhatsApp</a>
    </div>
  </div>
  """.format(wa=PRASAD_WHATSAPP),
  unsafe_allow_html=True
)

st.markdown(
  """
  <div class='mobile-bar'>
    {wa}WhatsApp</a>
    {ig}Instagram</a>
  </div>
  """.format(wa=PRASAD_WHATSAPP, ig=PRASAD_IG_URL),
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
  st.caption(f"Favorites: {len(st.session_state.favorites)}")

# Sticky filter bar (single grid ensures alignment)
st.markdown("<div class='filters'>", unsafe_allow_html=True)
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
  st.session_state.s_region = st.selectbox("Region", ["All"] + regions,
                                           index=(["All"] + regions).index(st.session_state.s_region))
with c2:
  st.session_state.s_condition = st.selectbox("Condition", ["All", "New", "Old"],
                                              index=["All","New","Old"].index(st.session_state.s_condition))
with c3:
  st.session_state.s_type = st.selectbox("Type", ["All", "Individual", "Apartment"],
                                         index=["All","Individual","Apartment"].index(st.session_state.s_type))
with c4:
  beds_opts = [0,1,2,3,4,5]
  idx = beds_opts.index(st.session_state.s_min_bed) if st.session_state.s_min_bed in beds_opts else 0
  st.session_state.s_min_bed = st.selectbox("Min bedrooms", beds_opts, index=idx)
with c5:
  # Budget slider honors session state (chips may set it)
  min_v, max_v = st.session_state.s_budget
  st.session_state.s_budget = st.slider("Budget (₹)", min_value=int(pmin_data), max_value=int(pmax_data),
                                        value=(int(min_v), int(max_v)), step=500_000)
with c6:
  sort_opts = ["Newest", "Price ↑", "Price ↓", "Area ↑", "Area ↓"]
  st.session_state.s_sort = st.selectbox("Sort", sort_opts, index=sort_opts.index(st.session_state.s_sort))
st.markdown("</div>", unsafe_allow_html=True)

# Search
st.markdown("<div class='search-wrap'>", unsafe_allow_html=True)
st.session_state.s_search = st.text_input("Search (title/address)", value=st.session_state.s_search)
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# Filter + sort functions
# --------------------------------------------------
def matches(p):
  s = st.session_state
  if s.s_region != "All" and p["region_key"] != s.s_region: return False
  if s.s_condition != "All" and p["condition"] != s.s_condition: return False
  if s.s_type != "All" and p["home_type"] != s.s_type: return False
  if s.s_min_bed and p.get("bedrooms", 0) < s.s_min_bed: return False
  bmin, bmax = s.s_budget
  if not (bmin <= p.get("price_inr", 0) <= bmax): return False
  qlc = (s.s_search or "").lower()
  if qlc and qlc not in (p.get("title","") + " " + p.get("address","")).lower(): return False
  return True

def sorter_key(p):
  s = st.session_state
  if s.s_sort == "Price ↑": return p.get("price_inr", 0)
  if s.s_sort == "Price ↓": return -p.get("price_inr", 0)
  if s.s_sort == "Area ↑": return p.get("area_sqft", 0)
  if s.s_sort == "Area ↓": return -p.get("area_sqft", 0)
  return -p.get("id", 0)  # Newest

filtered = sorted([p for p in data if matches(p)], key=sorter_key)

# --------------------------------------------------
# Dialog: Book a site visit
# --------------------------------------------------
@st.dialog("Book a site visit", width="large")
def book_visit_dialog(p):
  st.markdown("**{t}** · {r}".format(t=p['title'], r=p['region_key']))
  visit_date = st.date_input("Date", key="dlg_date_{id}".format(id=p["id"]))
  visit_time = st.time_input("Time", value=time(11,30), key="dlg_time_{id}".format(id=p["id"]))
  name = st.text_input("Your name", key="dlg_nm_{id}".format(id=p["id"]))
  phone = st.text_input("Phone", key="dlg_ph_{id}".format(id=p["id"]))
  email = st.text_input("Email", key="dlg_em_{id}".format(id=p["id"]))
  note = st.text_area("Note", key="dlg_nt_{id}".format(id=p["id"]))
  if st.button("Request visit", key="dlg_req_{id}".format(id=p["id"])):
    lead = {
      "ts": datetime.now().isoformat(timespec="seconds"),
      "property_id": p["id"], "title": p["title"], "region": p["region_key"],
      "name": name.strip(), "phone": phone.strip(), "email": email.strip(),
      "visit_date": str(visit_date), "visit_time": str(visit_time),
      "note": note.strip(), "source": "site_visit"
    }
    st.session_state.leads.append(lead)
    toast_ok("Visit requested (demo).")
    st.rerun()

# --------------------------------------------------
# Grid + actions
# --------------------------------------------------
if not filtered:
  st.warning("No properties match your filters.")
else:
  # Optional map view if lat/lng are present
  map_df = pd.DataFrame([
    {"lat": p.get("lat"), "lon": p.get("lng"), "title": p["title"], "price": p["price_inr"]}
    for p in filtered if p.get("lat") and p.get("lng")
  ])
  if not map_df.empty:
    st.markdown("### Map view")
    layer = pdk.Layer(
      "ScatterplotLayer", data=map_df, get_position='[lon, lat]',
      get_fill_color='[34, 211, 238, 160]', get_radius=60, pickable=True
    )
    vs = pdk.ViewState(latitude=float(map_df.lat.mean()), longitude=float(map_df.lon.mean()), zoom=12)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=vs,
                             tooltip={"text": "{title} — ₹{price}"}))

  cols = st.columns(3)  # stacks automatically on narrow screens
  for i, p in enumerate(filtered):
    with cols[i % 3]:
      st.container()
      st.image(p["image"], use_column_width=True)
      st.markdown("**{t}**".format(t=p['title']))
      st.markdown("<span class='price'>₹{n:,.0f}</span>".format(n=p['price_inr']), unsafe_allow_html=True)
      st.markdown(
        "<span class='badge'>{rk}</span><span class='badge'>{c}</span>"
        "<span class='badge'>{ht}</span><span class='badge'>{br} BR</span>"
        "<span class='badge'>{sf} sqft</span>".format(
          rk=p['region_key'], c=p['condition'], ht=p['home_type'],
          br=p.get('bedrooms',0), sf=p.get('area_sqft',0)
        ),
        unsafe_allow_html=True
      )
      dists = p.get("distances", {})
      if dists:
        st.markdown(" ".join(["<span class='badge'>{k}: {v}</span>".format(k=k, v=v) for k,v in dists.items()]),
                    unsafe_allow_html=True)

      st.caption(p.get("address", ""), help="Address")

      # Gallery (simple select "carousel")
      pics = [p["image"]] + p.get("images", [])
      if pics:
        sel = st.selectbox("Gallery", options=range(len(pics)),
                           format_func=lambda idx: "Photo {n}".format(n=idx+1),
                           key="gal_{id}".format(id=p['id']))
        st.image(pics[sel], use_column_width=True)

      # CTAs (unique keys to avoid duplicate element IDs)
      b1, b2, b3, b4 = st.columns(4)
      with b1:
        insta = p.get("insta_url", "")
        if insta:
          st.link_button("Instagram", url=insta, help="View post")
        else:
          st.button("Instagram", key="insta_disabled_{id}".format(id=p['id']), disabled=True)
      with b2:
        txt = quote_plus("Hi Prasad Realty, I'm interested in '{t}' in {r}.".format(t=p['title'], r=p['region_key']))
        utm = "utm_source=streamlit&utm_medium=cta&utm_campaign=prasad_demo"
        st.link_button("WhatsApp", url="{wa}?text={txt}&{utm}".format(wa=PRASAD_WHATSAPP, txt=txt, utm=utm))
      with b3:
        fav_key = "fav_{id}".format(id=p['id'])
        is_fav = p['id'] in st.session_state.favorites
        if st.button(("💙 Unfavorite" if is_fav else "❤️ Favorite"), key=fav_key):
          if is_fav:
            st.session_state.favorites.remove(p['id'])
            toast_ok("Removed from favorites")
          else:
            st.session_state.favorites.add(p['id'])
            toast_ok("Added to favorites")
      with b4:
        if st.button("Details", key="d_{id}".format(id=p['id'])):
          st.session_state["show_{id}".format(id=p['id'])] = not st.session_state.get("show_{id}".format(id=p['id']), False)

      # Details expander
      if st.session_state.get("show_{id}".format(id=p['id']), False):
        with st.expander("Details", expanded=True):
          st.write({k: v for k, v in p.items() if k != "image"})

          # EMI calculator
          st.markdown("**EMI Calculator**")
          emi1, emi2, emi3 = st.columns(3)
          with emi1:
            loan_amt = st.number_input("Loan amount (₹)", value=float(p["price_inr"]),
                                       min_value=0.0, step=100000.0, key="loan_{id}".format(id=p['id']))
          with emi2:
            rate = st.number_input("Interest (% p.a.)", value=8.5, min_value=0.0, step=0.1,
                                   key="rate_{id}".format(id=p['id']))
          with emi3:
            years = st.number_input("Tenure (years)", value=20, min_value=1, step=1,
                                    key="years_{id}".format(id=p['id']))
          r = (rate / 100.0) / 12.0
          n = int(years * 12)
          emi = 0 if n == 0 else loan_amt * r * ((1 + r)**n) / (((1 + r)**n) - 1)
          st.write("**Estimated EMI:** ₹{m:,.0f} / month".format(m=emi))

          # Site-visit dialog
          if st.button("Book visit", key="bk_{id}".format(id=p['id'])):
            book_visit_dialog(p)

# --------------------------------------------------
# Quick contact + CSV
# --------------------------------------------------
st.markdown("---")
st.subheader("Quick contact")
qc1, qc2, qc3 = st.columns([2,2,3])
with qc1: qn = st.text_input("Your name", key="qc_name")
with qc2: qp = st.text_input("Phone", key="qc_phone")
with qc3: qe = st.text_input("Email", key="qc_email")
msg = st.text_area("Message", key="qc_msg")

cc1, cc2 = st.columns(2)
with cc1:
  if st.button("Send message", key="send_msg"):
    lead = {
      "ts": datetime.now().isoformat(timespec="seconds"),
      "property_id": None, "title": None, "region": None,
      "name": qn.strip(), "phone": qp.strip(), "email": qe.strip(),
      "visit_date": "", "visit_time": "", "note": msg.strip(), "source": "contact_form"
    }
    st.session_state.leads.append(lead)
    toast_ok("Message saved (demo).")
with cc2:
  if st.session_state.leads:
    df = pd.DataFrame(st.session_state.leads)
    st.download_button("Download leads (CSV)",
                       data=df.to_csv(index=False).encode("utf-8"),
                       file_name="leads.csv", mime="text/csv")
  else:
    st.button("Download leads (CSV)", key="dl_disabled", disabled=True)

st.caption("Prasad Realty — Streamlit prototype · polished UI ·
