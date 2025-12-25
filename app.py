
# app.py — EstateVista x Prasad Realty demo
# Streamlit prototype tailored for a real estate demo with Instagram-forward CTAs.

import json
from pathlib import Path
from datetime import datetime, time
from urllib.parse import quote_plus
import streamlit as st
import pandas as pd

# --------------------
# Page / Theme Setup
# --------------------
st.set_page_config(page_title="EstateVista · Prasad Realty", page_icon="🏠", layout="wide")

CSS = """
<style>
:root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8; --accent:#22d3ee; --primary:#38bdf8; }
html, body, [class*="stApp"] { background: linear-gradient(135deg, #0b1020, var(--bg)); color: var(--text); }
.block-container { padding-top: 1.0rem; }
.brand-card { border-radius: 14px; background: rgba(17,24,39,0.7); border: 1px solid #1f2937; padding: 12px; }
.badge { display:inline-block; margin-right:6px; margin-top:6px; padding:4px 8px; border-radius:999px; border:1px solid #334155; color: var(--muted); font-size:12px; }
.price { font-weight:700; color: var(--accent); }
.button-primary { background: linear-gradient(135deg, var(--primary), var(--accent)); color:#0b1220; border:0; padding:8px 12px; border-radius:8px; font-weight:600; }
.hero { border-radius: 14px; background: rgba(17,24,39,0.7); border: 1px solid #1f2937; padding: 16px; margin-bottom: 8px; }
.card { border-radius: 16px; background: rgba(17,24,39,0.7); border: 1px solid #1f2937; padding: 12px; }
.small { color: var(--muted); font-size:13px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------
# Branding / Constants
# --------------------
PRASAD_IG_HANDLE = "prasad.realty_vizag"   # Instagram handle observed publicly
PRASAD_IG_URL = f"https://instagram.com/{PRASAD_IG_HANDLE}"
PRASAD_PHONE = "+916309729493"             # phone from public Prasad Realty content
PRASAD_WHATSAPP = "https://wa.me/916309729493"

# --------------------
# Session State
# --------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "rerun" not in st.session_state:
    st.session_state.rerun = False
if "leads" not in st.session_state:
    st.session_state.leads = []  # list of dicts

# --------------------
# Sidebar: Login + Brand
# --------------------
with st.sidebar:
    st.title("🏠 EstateVista")
    st.caption("Demo for Prasad Realty")

    # Brand card
    with st.container():
        st.markdown(
            f"""
            <div class='brand-card'>
              <div style='display:flex;align-items:center;justify-content:space-between;gap:8px;'>
                <div>
                  <div style='font-weight:700;'>Prasad Realty</div>
                  <div class='small'>Visakhapatnam · Residential & Plots</div>
                </div>
                {PRASAD_IG_URL}Instagram</a>
              </div>
              <div style='margin-top:8px;' class='small'>Call / WhatsApp: {PRASAD_PHONE}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Mock login
    if st.session_state.user:
        st.success(f"Signed in as {st.session_state.user}")
        if st.button("Sign out"):
            st.session_state.user = None
            st.session_state.rerun = True
    else:
        name = st.text_input("Your name")
        if st.button("Continue"):
            if name.strip():
                st.session_state.user = name.strip()
                st.session_state.rerun = True
            else:
                st.error("Please enter a name")

    # Safe rerun
    if st.session_state.rerun:
        st.session_state.rerun = False
        st.rerun()

# Gate until login
if not st.session_state.user:
    st.info("Please login from the left sidebar to continue.")
    st.stop()

# --------------------
# Data: properties.json or fallback
# --------------------
DATA_PATH = Path(__file__).parent / "properties.json"

MOCK_PROPERTIES = [
    # region_key, condition, home_type, price_inr, bedrooms, area_sqft, image, insta_url (optional)
    {"id":1,"title":"2BHK near park","region_key":"Visalakshinagar","condition":"New","home_type":"Apartment",
     "bedrooms":2,"bathrooms":2,"area_sqft":980,"price_inr":6500000,"address":"Plot 23, Visalakshinagar",
     "image":"https://picsum.photos/seed/visalakshi1/800/500","insta_url":""},
    {"id":2,"title":"Independent 3BHK","region_key":"Hanumanthawaka","condition":"Old","home_type":"Individual",
     "bedrooms":3,"bathrooms":3,"area_sqft":1700,"price_inr":11000000,"address":"Colony Rd, Hanumanthawaka",
     "image":"https://picsum.photos/seed/hanuman3/800/500","insta_url":""},
    {"id":3,"title":"MVP 2BHK corner flat","region_key":"MVP Colony","condition":"New","home_type":"Apartment",
     "bedrooms":2,"bathrooms":2,"area_sqft":1050,"price_inr":7800000,"address":"Sector 5, MVP Colony",
     "image":"https://picsum.photos/seed/mvp1/800/500","insta_url":""},
    {"id":4,"title":"Luxury 4BHK penthouse","region_key":"MVP Colony","condition":"New","home_type":"Apartment",
     "bedrooms":4,"bathrooms":4,"area_sqft":2200,"price_inr":32000000,"address":"Sector 1, MVP Colony",
     "image":"https://picsum.photos/seed/mvp4/800/500","insta_url":""},
]

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = MOCK_PROPERTIES

# --------------------
# Hero: quick chips + mini CTA
# --------------------
st.markdown(
    """
    <div class='hero'>
      <div style='display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;'>
        <div>
          <div style='font-weight:800;font-size:20px;'>Find your home in Vizag</div>
          <div class='small'>Filter by area, price, and home type. Book a site visit in one click.</div>
        </div>
        <a href='""" + PRASAD_WHATSAPP + """' target='_blank' class='button-primary'>WhatsApp</a>
      </div>
    </div>
    """, unsafe_allow_html=True
)

# --------------------
# Filters (sidebar-like, but on top)
# --------------------
regions = sorted({p["region_key"] for p in data})
c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])

with c1:
    region_sel = st.selectbox("Region", ["All"] + regions, index=0)

with c2:
    condition_sel = st.selectbox("Condition", ["All", "New", "Old"], index=0)

with c3:
    home_type_sel = st.selectbox("Type", ["All", "Individual", "Apartment"], index=0)

with c4:
    min_bed = st.selectbox("Min bedrooms", [0,1,2,3,4,5], index=0)

with c5:
    # Take dynamic min/max from data
    prices = [p["price_inr"] for p in data]
    pmin = min(prices) if prices else 0
    pmax = max(prices) if prices else 0
    price_range = st.slider("Budget (₹)", min_value=int(pmin), max_value=int(pmax or 10000000),
                            value=(int(pmin), int(pmax or 10000000)), step=500000)

with c6:
    sort_by = st.selectbox("Sort", ["Newest", "Price ↑", "Price ↓", "Area ↑", "Area ↓"], index=0)

search_q = st.text_input("Search (title/address)")

# --------------------
# Filter logic
# --------------------
def matches(p):
    if region_sel != "All" and p["region_key"] != region_sel:
        return False
    if condition_sel != "All" and p["condition"] != condition_sel:
        return False
    if home_type_sel != "All" and p["home_type"] != home_type_sel:
        return False
    if min_bed and p.get("bedrooms", 0) < min_bed:
        return False
    if not (price_range[0] <= p.get("price_inr", 0) <= price_range[1]):
        return False
    qlc = (search_q or "").lower()
    if qlc and qlc not in (p.get("title","") + " " + p.get("address","")).lower():
        return False
    return True

filtered = [p for p in data if matches(p)]

def sorter_key(p):
    if sort_by == "Price ↑":
        return p.get("price_inr", 0)
    if sort_by == "Price ↓":
        return -p.get("price_inr", 0)
    if sort_by == "Area ↑":
        return p.get("area_sqft", 0)
    if sort_by == "Area ↓":
        return -p.get("area_sqft", 0)
    # "Newest" fallback: descending id
    return -p.get("id", 0)

filtered = sorted(filtered, key=sorter_key)

# --------------------
# Render grid + actions
# --------------------
if not filtered:
    st.warning("No properties match your filters.")
else:
    cols = st.columns(3)
    for i, p in enumerate(filtered):
        with cols[i % 3]:
            st.image(p["image"], use_column_width=True)
            st.markdown(f"**{p['title']}**")
            st.markdown(f"<span class='price'>₹{p['price_inr']:,.0f}</span>", unsafe_allow_html=True)
            st.markdown(
                f"<span class='badge'>{p['region_key']}</span>"
                f"<span class='badge'>{p['condition']}</span>"
                f"<span class='badge'>{p['home_type']}</span>"
                f"<span class='badge'>{p.get('bedrooms',0)} BR</span>"
                f"<span class='badge'>{p.get('area_sqft',0)} sqft</span>",
                unsafe_allow_html=True
            )
            st.caption(p.get("address", ""))

            b1, b2, b3 = st.columns(3)
            with b1:
                # View on Instagram (if available)
                insta = p.get("insta_url", "")
                if insta:
                    st.link_button("Instagram", url=insta, help="View post")
                else:
                    st.button("Instagram", disabled=True)
            with b2:
                # WhatsApp prefilled
                text = quote_plus(f"Hi Prasad Realty, I'm interested in '{p['title']}' in {p['region_key']}.")
                st.link_button("WhatsApp", url=f"{PRASAD_WHATSAPP}?text={text}")
            with b3:
                # Toggle details
                if st.button("Details", key=f"details_{p['id']}"):
                    st.session_state[f"show_{p['id']}"] = not st.session_state.get(f"show_{p['id']}", False)

            if st.session_state.get(f"show_{p['id']}", False):
                with st.expander("Details", expanded=True):
                    details = {k: v for k, v in p.items() if k != "image"}
                    st.write(details)

                    # Book a site visit
                    st.markdown("**Book a site visit**")
                    visit_date = st.date_input("Date", key=f"date_{p['id']}")
                    visit_time = st.time_input("Time", value=time(11, 30), key=f"time_{p['id']}")
                    name = st.text_input("Your name", key=f"nm_{p['id']}")
                    phone = st.text_input("Phone", key=f"ph_{p['id']}")
                    email = st.text_input("Email", key=f"em_{p['id']}")
                    note = st.text_area("Note (optional)", key=f"nt_{p['id']}")

                    cta1, cta2 = st.columns(2)
                    with cta1:
                        if st.button("Request visit", key=f"req_{p['id']}"):
                            lead = {
                                "ts": datetime.now().isoformat(timespec="seconds"),
                                "property_id": p["id"],
                                "title": p["title"],
                                "region": p["region_key"],
                                "name": name.strip(),
                                "phone": phone.strip(),
                                "email": email.strip(),
                                "visit_date": str(visit_date),
                                "visit_time": str(visit_time),
                                "note": note.strip(),
                                "source": "site_visit"
                            }
                            st.session_state.leads.append(lead)
                            st.success("Visit requested. (Demo: stored locally)")
                    with cta2:
                        msg = quote_plus(f"Visit request for '{p['title']}' on {visit_date} at {visit_time}. Name: {name}, Phone: {phone}")
                        st.link_button("WhatsApp confirm", url=f"{PRASAD_WHATSAPP}?text={msg}")

# --------------------
# Lead capture block (global)
# --------------------
st.markdown("---")
st.subheader("Quick contact")
qc1, qc2, qc3 = st.columns([2,2,3])
with qc1:
    qn = st.text_input("Your name", key="qc_name")
with qc2:
    qp = st.text_input("Phone", key="qc_phone")
with qc3:
    qe = st.text_input("Email", key="qc_email")

msg = st.text_area("Message", key="qc_msg")
cc1, cc2 = st.columns(2)
with cc1:
    if st.button("Send message"):
        lead = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "property_id": None,
            "title": None,
            "region": None,
            "name": qn.strip(),
            "phone": qp.strip(),
            "email": qe.strip(),
            "visit_date": "",
            "visit_time": "",
            "note": msg.strip(),
            "source": "contact_form"
        }
        st.session_state.leads.append(lead)
        st.success("Message saved (demo).")
with cc2:
    # Export leads CSV
    if st.session_state.leads:
        df = pd.DataFrame(st.session_state.leads)
        st.download_button("Download leads (CSV)", data=df.to_csv(index=False).encode("utf-8"),
                           file_name="leads.csv", mime="text/csv")
    else:
        st.button("Download leads (CSV)", disabled=True)

st.caption("Prototype — Stream.")
