# streamlit-realestate/app.py
import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="EstateVista — Streamlit", page_icon="🏠", layout="wide")

# ---- Styles ----
CUSTOM_CSS = """
<style>
:root { --bg:#0f172a; --panel:#111827; --text:#e5e7eb; --muted:#94a3b8; --accent:#22d3ee; }
html, body, [class*="stApp"] { background: linear-gradient(135deg, #0b1020, var(--bg)); color: var(--text); }
.block-container { padding-top: 1.5rem; }
.card { border-radius: 16px; background: rgba(17,24,39,0.7); border: 1px solid #1f2937; padding: 1rem; }
.badge { display:inline-block; margin-right:6px; margin-top:6px; padding:4px 8px; border-radius:999px; border:1px solid #334155; color: var(--muted); font-size:12px; }
.price { font-weight:700; color: var(--accent); }
input, select, textarea { color: #e5e7eb; }
.stSelectbox > div > div { color: #e5e7eb; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---- Mock login (session state) ----
if 'user' not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.title("🏠 EstateVista")
    if st.session_state.user:
        st.success(f"Signed in as {st.session_state.user}")
        if st.button("Sign out"):
            st.session_state.user = None
            st.experimental_rerun()
    else:
        st.caption("Mock login — enter any name")
        name = st.text_input("Your name", value="")
        if st.button("Continue"):
            if name.strip():
                st.session_state.user = name.strip()
                st.experimental_rerun()
            else:
                st.error("Please enter a name")

if not st.session_state.user:
    st.info("Please login from the left sidebar to continue.")
    st.stop()

# ---- Load data ----
DATA_PATH = Path(__file__).parent / 'properties.json'
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ---- Filters ----
regions = sorted({p['region_key'] for p in data})
col1, col2, col3, col4 = st.columns([1,1,1,1])
with col1:
    region_sel = st.selectbox("Region", options=["All"] + regions, index=0)
with col2:
    condition_sel = st.selectbox("Condition", options=["All", "New", "Old"], index=0)
with col3:
    home_type_sel = st.selectbox("Home Type", options=["All", "Individual", "Apartment"], index=0)
with col4:
    q = st.text_input("Search (title/address)", value="")

# ---- Filter logic ----
q_lc = (q or '').lower()
filtered = [p for p in data if
    (region_sel == "All" or p['region_key'] == region_sel) and
    (condition_sel == "All" or p['condition'] == condition_sel) and
    (home_type_sel == "All" or p['home_type'] == home_type_sel) and
    (not q_lc or (p['title'] + ' ' + p['address']).lower().find(q_lc) >= 0)
]

# ---- Render grid ----
if len(filtered) == 0:
    st.warning("No properties match your filters.")
else:
    # 3-column responsive grid
    cols = st.columns(3)
    for i, p in enumerate(filtered):
        with cols[i % 3]:
            with st.container():
                st.image(p['image'], use_column_width=True)
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
                st.caption(p['address'])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Details", key=f"d_{p['id']}"):
                        st.session_state[f"show_{p['id']}"] = True
                with c2:
                    if st.button("Contact", key=f"c_{p['id']}"):
                        st.session_state[f"contact_{p['id']}"] = True

                # Details modal-ish section
                if st.session_state.get(f"show_{p['id']}"):
                    with st.expander("Details", expanded=True):
                        st.write({k: v for k, v in p.items() if k not in ['image']})
                        if st.button("Close", key=f"close_{p['id']}"):
                            st.session_state[f"show_{p['id']}"] = False

                # Contact form inline
                if st.session_state.get(f"contact_{p['id']}"):
                    with st.expander("Contact seller", expanded=True):
                        nm = st.text_input("Your name", key=f"nm_{p['id']}")
                        ph = st.text_input("Phone", key=f"ph_{p['id']}")
                        msg = st.text_area("Message", key=f"msg_{p['id']}")
                        if st.button("Send", key=f"send_{p['id']}"):
                            st.success("(Demo) Lead captured locally. In real app, this would POST to backend.")
                        if st.button("Close contact", key=f"closec_{p['id']}"):
                            st.session_state[f"contact_{p['id']}"] = False

st.caption("Prototype — Streamlit app, static JSON, client-side filtering.")
