import streamlit as st

st.set_page_config(
    page_title="Voyager — Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
import os
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.storage import TripStorage
from utils.helpers import get_trip_status, format_date_range, get_trip_days, get_days_until


# ─── Session State Init ────────────────────────────────────────────────
def _init():
    defaults = {
        "page": "dashboard",
        "current_trip_id": None,
        "show_create_form": False,
        "editing_trip_id": None,
        "expand_add_activity": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ─── Storage (cached singleton) ────────────────────────────────────────
@st.cache_resource
def _get_storage() -> TripStorage:
    return TripStorage()

storage = _get_storage()


# ─── CSS ───────────────────────────────────────────────────────────────
css_path = ROOT / "assets" / "style.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)


# ─── Sidebar ───────────────────────────────────────────────────────────
def _nav_button(page_id: str, icon: str, label: str):
    active = st.session_state.page == page_id
    if st.button(
        f"{icon}  {label}",
        key=f"nav_{page_id}",
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        st.session_state.page = page_id
        st.rerun()


with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <span class="logo-icon">✈️</span>
        <div class="logo-text">
            <span class="logo-name">Voyager</span>
            <span class="logo-tagline">Trip Planner</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Active Trip Selector ────────────────────────────────────────
    trips = storage.get_all_trips()
    st.markdown("<div class='sidebar-section-label'>ACTIVE TRIP</div>", unsafe_allow_html=True)

    if trips:
        names = ["— Select a trip —"] + [t["name"] for t in trips]
        ids   = [None] + [t["id"] for t in trips]

        cur_idx = 0
        if st.session_state.current_trip_id:
            try:
                cur_idx = ids.index(st.session_state.current_trip_id)
            except ValueError:
                cur_idx = 0

        chosen = st.selectbox("Trip", names, index=cur_idx, label_visibility="collapsed", key="sb_trip")
        new_id = ids[names.index(chosen)]
        if new_id != st.session_state.current_trip_id:
            st.session_state.current_trip_id = new_id
            st.rerun()

        # Show mini info for selected trip
        if st.session_state.current_trip_id:
            t = storage.get_trip(st.session_state.current_trip_id)
            if t:
                status = get_trip_status(t)
                sc = {"Planning":"#6b7280","Upcoming":"#4a8cf0","Active":"#10c97a","Completed":"#9b6cf8"}.get(status,"#6b7280")
                dr = format_date_range(t.get("start_date",""), t.get("end_date",""))
                days_n = get_trip_days(t.get("start_date",""), t.get("end_date",""))
                st.markdown(f"""
                <div style="background:#0d0f19;border:1px solid #181e30;border-radius:8px;padding:8px 10px;margin:4px 0 8px 0;">
                    <div style="font-size:0.78rem;font-weight:600;color:#edf0fc;">{t.get("cover_emoji","✈️")} {t["name"]}</div>
                    <div style="font-size:0.7rem;color:#7c88a8;margin-top:2px;">{dr} · {days_n}d</div>
                    <div style="margin-top:4px;"><span style="font-size:0.65rem;padding:2px 7px;border-radius:99px;background:{sc}20;color:{sc};border:1px solid {sc}40;">{status}</span></div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='font-size:0.78rem;color:#4a5568;padding:4px 0 8px 0;'>No trips yet.</p>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── Navigation ─────────────────────────────────────────────────
    st.markdown("<div class='sidebar-section-label'>NAVIGATION</div>", unsafe_allow_html=True)
    _nav_button("dashboard", "🏠", "Dashboard")
    _nav_button("trips",     "✈️", "My Trips")
    _nav_button("itinerary", "📅", "Itinerary")
    _nav_button("budget",    "💰", "Budget")
    _nav_button("map",       "🗺️", "Map")
    _nav_button("packing",   "🎒", "Packing List")
    _nav_button("export",    "📄", "Export PDF")

    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    # ── Quick Stats ─────────────────────────────────────────────────
    st.markdown("<div class='sidebar-section-label'>QUICK STATS</div>", unsafe_allow_html=True)
    total    = len(trips)
    upcoming = sum(1 for t in trips if get_trip_status(t) == "Upcoming")
    active   = sum(1 for t in trips if get_trip_status(t) == "Active")

    qc1, qc2, qc3 = st.columns(3)
    with qc1: st.metric("Trips",    total)
    with qc2: st.metric("Upcoming", upcoming)
    with qc3: st.metric("Active",   active)

    # Upcoming countdown
    upcoming_trips = sorted(
        [t for t in trips if get_trip_status(t) == "Upcoming"],
        key=lambda t: t.get("start_date","")
    )
    if upcoming_trips:
        next_trip = upcoming_trips[0]
        days_left = get_days_until(next_trip["start_date"])
        st.markdown(f"""
        <div style="background:rgba(74,140,240,0.08);border:1px solid rgba(74,140,240,0.2);
                    border-radius:8px;padding:8px 10px;margin-top:8px;text-align:center;">
            <div style="font-size:0.65rem;color:#4a8cf0;text-transform:uppercase;letter-spacing:0.08em;">Next Trip In</div>
            <div style="font-family:'Sora',sans-serif;font-size:1.6rem;font-weight:700;color:#4a8cf0;line-height:1.2;">{days_left}</div>
            <div style="font-size:0.65rem;color:#4a5568;">days</div>
            <div style="font-size:0.72rem;color:#7c88a8;margin-top:2px;">{next_trip["name"]}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── Page Router ───────────────────────────────────────────────────────
page = st.session_state.page

if page == "dashboard":
    from views.dashboard   import show_dashboard;   show_dashboard(storage)
elif page == "trips":
    from views.trips       import show_trips;       show_trips(storage)
elif page == "itinerary":
    from views.itinerary   import show_itinerary;   show_itinerary(storage)
elif page == "budget":
    from views.budget      import show_budget;      show_budget(storage)
elif page == "map":
    from views.map_view    import show_map;         show_map(storage)
elif page == "packing":
    from views.packing     import show_packing;     show_packing(storage)
elif page == "export":
    from views.export_page import show_export;      show_export(storage)
