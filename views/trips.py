import streamlit as st
from datetime import date, timedelta
from utils.helpers import (
    get_trip_status, format_date_range, get_trip_days,
    format_currency, get_status_color,
    TRIP_TYPES, CURRENCIES, COVER_EMOJIS,
)


def show_trips(storage):
    trips = storage.get_all_trips()

    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">My Trips</h1>
        <p class="page-subtitle">Create and manage all your travel adventures.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Create / Edit Toggle ─────────────────────────────────────────
    editing_id = st.session_state.get("editing_trip_id", None)
    show_form  = st.session_state.get("show_create_form", False) or editing_id is not None

    col_hdr, col_btn = st.columns([4, 1])
    with col_btn:
        if not show_form:
            if st.button("➕ New Trip", type="primary", use_container_width=True):
                st.session_state.show_create_form = True
                st.session_state.editing_trip_id  = None
                st.rerun()
        else:
            if st.button("✕ Cancel", use_container_width=True):
                st.session_state.show_create_form = False
                st.session_state.editing_trip_id  = None
                st.rerun()

    # ── Form ─────────────────────────────────────────────────────────
    if show_form:
        editing_trip = storage.get_trip(editing_id) if editing_id else None
        mode = "Edit Trip" if editing_trip else "New Trip"

        st.markdown(f"<div class='form-card'><div class='form-title'>{'✏️' if editing_trip else '✈️'} {mode}</div>", unsafe_allow_html=True)

        with st.form("trip_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Trip Name *", value=editing_trip.get("name","") if editing_trip else "", placeholder="e.g. Tokyo Adventure 2025")
                destination = st.text_input("Destination *", value=editing_trip.get("destination","") if editing_trip else "", placeholder="e.g. Tokyo, Japan")
                trip_type = st.selectbox("Trip Type", TRIP_TYPES,
                    index=TRIP_TYPES.index(editing_trip["trip_type"]) if editing_trip and editing_trip.get("trip_type") in TRIP_TYPES else 0)
                travelers = st.number_input("Number of Travelers", min_value=1, max_value=50,
                    value=editing_trip.get("travelers",2) if editing_trip else 2)

            with c2:
                default_start = date.today() + timedelta(days=30)
                default_end   = default_start + timedelta(days=7)
                if editing_trip:
                    from utils.helpers import parse_date
                    ds = parse_date(editing_trip.get("start_date","")) or default_start
                    de = parse_date(editing_trip.get("end_date",""))   or default_end
                else:
                    ds, de = default_start, default_end

                start_date = st.date_input("Start Date *", value=ds)
                end_date   = st.date_input("End Date *",   value=de)

                col_cur, col_bud = st.columns(2)
                with col_cur:
                    currency = st.selectbox("Currency", CURRENCIES,
                        index=CURRENCIES.index(editing_trip["currency"]) if editing_trip and editing_trip.get("currency") in CURRENCIES else 0)
                with col_bud:
                    budget = st.number_input("Total Budget", min_value=0.0,
                        value=float(editing_trip.get("budget",1000)) if editing_trip else 1000.0, step=100.0)

                emoji_label = "Cover Emoji"
                emoji_idx = COVER_EMOJIS.index(editing_trip["cover_emoji"]) if editing_trip and editing_trip.get("cover_emoji") in COVER_EMOJIS else 0
                cover_emoji = st.selectbox(emoji_label, COVER_EMOJIS, index=emoji_idx)

            description = st.text_area("Notes / Description", value=editing_trip.get("description","") if editing_trip else "",
                placeholder="Any details, notes, or things to remember about this trip…", height=80)

            submitted = st.form_submit_button("💾 Save Trip" if editing_trip else "✈️ Create Trip", type="primary", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.error("Trip name is required.")
                elif not destination.strip():
                    st.error("Destination is required.")
                elif start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    trip_data = {
                        "name": name.strip(),
                        "destination": destination.strip(),
                        "trip_type": trip_type,
                        "travelers": travelers,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "currency": currency,
                        "budget": budget,
                        "cover_emoji": cover_emoji,
                        "description": description.strip(),
                    }
                    if editing_trip:
                        storage.update_trip(editing_id, trip_data)
                        st.success("✅ Trip updated!")
                    else:
                        new_trip = storage.create_trip(trip_data)
                        st.session_state.current_trip_id = new_trip["id"]
                        st.success("✅ Trip created!")

                    st.session_state.show_create_form = False
                    st.session_state.editing_trip_id  = None
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Trip List ────────────────────────────────────────────────────
    if not trips:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">✈️</div>
            <div class="empty-title">No trips yet</div>
            <div class="empty-subtitle">Click "New Trip" above to plan your first adventure!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Sort by date descending
    sorted_trips = sorted(trips, key=lambda t: t.get("start_date",""), reverse=True)

    # Filter by status
    all_statuses = ["All", "Planning", "Upcoming", "Active", "Completed"]
    selected_status = st.selectbox("Filter by status", all_statuses, label_visibility="collapsed")

    for trip in sorted_trips:
        status = get_trip_status(trip)
        if selected_status != "All" and status != selected_status:
            continue

        sc = get_status_color(status)
        days = get_trip_days(trip.get("start_date",""), trip.get("end_date",""))
        dr = format_date_range(trip.get("start_date",""), trip.get("end_date",""))
        budget = format_currency(trip.get("budget",0), trip.get("currency","USD"))
        spent = sum(e.get("amount",0) for e in trip.get("expenses",[]))
        spent_fmt = format_currency(spent, trip.get("currency","USD"))
        activities_count = sum(len(v) for v in trip.get("itinerary",{}).values())
        packing_total = len(trip.get("packing_list",[]))
        packing_done  = sum(1 for i in trip.get("packing_list",[]) if i.get("packed"))

        with st.expander(f"{trip.get('cover_emoji','✈️')}  {trip['name']} — {trip.get('destination','')}", expanded=False):
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Duration", f"{days} days")
            with r2:
                st.metric("Budget", budget)
            with r3:
                st.metric("Spent", spent_fmt)
            with r4:
                st.metric("Activities", activities_count)

            st.markdown(f"""
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0;">
                <span class="status-badge" style="background:{sc}20;color:{sc};border:1px solid {sc}40;">{status}</span>
                <span style="font-size:0.78rem;color:#7c88a8;">📅 {dr}</span>
                <span style="font-size:0.78rem;color:#7c88a8;">👥 {trip.get('travelers',1)} travelers</span>
                <span style="font-size:0.78rem;color:#7c88a8;">🏷️ {trip.get('trip_type','')}</span>
            </div>
            """, unsafe_allow_html=True)

            if trip.get("description"):
                st.markdown(f"<p style='color:#7c88a8;font-size:0.82rem;'>{trip['description']}</p>", unsafe_allow_html=True)

            if packing_total > 0:
                pct = packing_done / packing_total * 100
                st.markdown(f"""
                <div>
                    <div class="progress-header"><span class="progress-label">🎒 Packing</span><span class="progress-value">{packing_done}/{packing_total}</span></div>
                    <div class="progress-track"><div class="progress-fill" style="width:{pct:.0f}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("📅 Itinerary", key=f"t_itin_{trip['id']}", use_container_width=True):
                    st.session_state.current_trip_id = trip["id"]
                    st.session_state.page = "itinerary"
                    st.rerun()
            with b2:
                if st.button("💰 Budget", key=f"t_budg_{trip['id']}", use_container_width=True):
                    st.session_state.current_trip_id = trip["id"]
                    st.session_state.page = "budget"
                    st.rerun()
            with b3:
                if st.button("✏️ Edit", key=f"t_edit_{trip['id']}", use_container_width=True):
                    st.session_state.editing_trip_id  = trip["id"]
                    st.session_state.show_create_form = False
                    st.rerun()
            with b4:
                confirm_key = f"confirm_del_{trip['id']}"
                if st.session_state.get(confirm_key, False):
                    if st.button("⚠️ Confirm Delete", key=f"t_cfm_{trip['id']}", use_container_width=True):
                        if st.session_state.current_trip_id == trip["id"]:
                            st.session_state.current_trip_id = None
                        storage.delete_trip(trip["id"])
                        st.session_state[confirm_key] = False
                        st.rerun()
                else:
                    if st.button("🗑️ Delete", key=f"t_del_{trip['id']}", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
