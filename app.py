
# app.py — EstateVista (Streamlit prototype)

import json
from pathlib import Path
import streamlit as st

# --------------------
# Page / Theme Setup
# --------------------
st.set_page_config(page_title="EstateVista — Streamlit", page_icon="🏠", layout="wide")

CUSTOM_CSS = """
<style>
:root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8; --accent:#22d3ee; }
html, body, [class*="stApp"] { background: linear-gradient(135deg, #0b1020, var(--bg)); color: var(--text); }
.block-container { padding-top: 1.2rem; }
.card { border-radius: 16px; background: rgba(17,24,39,0.7); border: 1px solid #1f2937; padding: 1rem; }
.badge { display:inline-block; margin-right:6px; margin-top:6px; padding:4px 8px; border-radius:999px; border:1px solid #334155; color: var(--muted); font-size:12px; }
.price { font-weight:700; color: var(--accent); }
input, select, textarea { color: #e5e7eb; }
.stSelectbox > div > div { color: #e5e7eb; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------
# Session State Defaults
# --------------------
if "user" not in st.session_state:
    st.session_state.user = None

# Flag used to trigger rerun **outside** callbacks
if "do_rerun" not in st.session_state:
    st.session_state.do_rerun = False

# Per-card UI state maps (details/contact)
if "show_details" not in st.session_state:
    st.session_state.show_details = {}  # {property_id: bool}
if "show_contact" not in st.session_state:
    st.session_state.show_contact = {}  # {property_id: bool}

# --------------------
# Sidebar: Mock Login
# --------------------
with st.sidebar:
    st.title("🏠 EstateVista")

    if st.session_state.user:
        st.success(f"Signed in as {st.session_state.user}")
        if st.button("Sign out"):
            st.session_state.user = None
            # Trigger rerun safely outside callback
            st.session_state.do_rerun = True
    else:
        st.caption("Mock login — enter any name")
        name = st.text_input("Your name", value="")
        if st.button("Continue"):
            if name.strip():
                st.session_state.user = name.strip()
                # Trigger rerun safely outside callback
                st.session_state.do_rerun = True
            else:
                st.error("Please enter a name")

# Perform rerun from the main body (safe place)
if st.session_state.do_rerun:
    st.session_state.do_rerun = False
    st.rerun()

# Gate the app until logged in
if not st.session_state.user:
    st.info("Please login from the left sidebar to continue.")
    st.stop()

# --------------------
# Load Data
# --------------------
DATA_PATH = Path(__file__).parent / "properties.json"
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    st.error(f"Couldn't find {DATA_PATH.name}. Make sure it sits next to app.py.")
    st.stop()
except json.JSONDecodeError as e:
    st.error(f"Failed to parse properties.json: {e}")
    st.stop()

# --------------------
# Filters
# --------------------
regions = sorted({p["region_key"] for p in data})

col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    region_sel = st.selectbox("Region", options=["All"] + regions, index=0)
with col2:
    condition_sel = st.selectbox("Condition", options=["All", "New", "Old"], index=0)
with col3:
    home_type_sel = st.selectbox("Home Type", options=["All", "Individual", "Apartment"], index=0)
with col4:
    q = st.text_input("Search (title/address)", value="")

# --------------------
# Filter Logic
# --------------------
q_lc = (q or "").lower()
filtered = [
    p for p in data
    if (region_sel == "All" or p["region_key"] == region_sel)
    and (condition_sel == "All" or p["condition"] == condition_sel)
    and (home_type_sel == "All" or p["home_type"] == home_type_sel)
    and (not q_lc or (p["title"] + " " + p["address"]).lower().find(q_lc) >= 0)
]

# --------------------
# Grid Renderer
# --------------------
if len(filtered) == 0:
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
                f"<span class='badge'>{p['bedrooms']} BR</span>"
                f"<span class='badge'>{p['area_sqft']} sqft</span>",
                unsafe_allow_html=True
            )
            st.caption(p["address"])

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Details", key=f"d_{p['id']}"):
                    st.session_state.show_details[p["id"]] = not st.session_state.show_details.get(p["id"], False)
            with c2:
                if st.button("Contact", key=f"c_{p['id']}"):
                    st.session_state.show_contact[p["id"]] = not st.session_state.show_contact.get(p["id"], False)

            # Details Section
            if st.session_state.show_details.get(p["id"]):
                with st.expander("Details", expanded=True):
                    # Show all fields except 'image'
                    details = {k: v for k, v in p.items() if k != "image"}
                    st.write(details)

            # Contact Section
            if st.session_state.show_contact.get(p["id"]):
                with st.expander("Contact seller", expanded=True):
                    nm = st.text_input("Your name", key=f"nm_{p['id']}")
                    ph = st.text_input("Phone", key=f"ph_{p['id']}")
                    msg = st.text_area("Message", key=f"msg_{p['id']}")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Send", key=f"send_{p['id']}"):
                            # Demo only — no backend call here
                            st.success("Lead captured locally (demo). In a real app, this would                            st.success("Lead captured locally (demo). In a real app, this would POST to a backend.")
                    with cc2:
                        if st.button("Close contact", key=f"closec_{p['id']}"):
                            # ✅ ensure this is one clean line:
                            st.session_state.show_contact[p["id"]] = False

