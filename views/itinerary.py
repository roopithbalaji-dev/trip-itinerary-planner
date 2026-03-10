import streamlit as st
from utils.helpers import (
    get_all_trip_dates, format_date, format_currency,
    ACTIVITY_CATEGORIES, ACTIVITY_ICONS, TIME_SLOTS, SLOT_MAP, SLOT_EMOJI, CURRENCIES,
)


def _no_trip():
    st.markdown("""
    <div class="info-banner">
        ℹ️ Select a trip from the sidebar to manage its itinerary.
    </div>
    """, unsafe_allow_html=True)


def show_itinerary(storage):
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📅 Itinerary Builder</h1>
        <p class="page-subtitle">Plan every moment — day by day, slot by slot.</p>
    </div>
    """, unsafe_allow_html=True)

    trip_id = st.session_state.get("current_trip_id")
    if not trip_id:
        _no_trip()
        return

    trip = storage.get_trip(trip_id)
    if not trip:
        _no_trip()
        return

    dates = get_all_trip_dates(trip)
    if not dates:
        st.warning("Trip has no valid dates. Please edit the trip first.")
        return

    currency = trip.get("currency", "USD")
    itinerary = trip.get("itinerary", {})

    # ── Day Selector ────────────────────────────────────────────────
    date_options = [d.strftime("%A, %b %d") for d in dates]
    date_strs    = [str(d) for d in dates]

    c_sel, c_info = st.columns([2, 3])
    with c_sel:
        chosen_label = st.selectbox("Select Day", date_options, label_visibility="visible")
        chosen_idx   = date_options.index(chosen_label)
        chosen_str   = date_strs[chosen_idx]
        chosen_date  = dates[chosen_idx]

    day_activities = itinerary.get(chosen_str, [])
    total_cost = sum(a.get("cost", 0) for a in day_activities)

    with c_info:
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("Day", f"{chosen_idx + 1} of {len(dates)}")
        with m2: st.metric("Activities", len(day_activities))
        with m3: st.metric("Day Cost", format_currency(total_cost, currency))

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Add Activity Form ────────────────────────────────────────────
    with st.expander("➕ Add Activity", expanded=st.session_state.get("expand_add_activity", False)):
        st.session_state["expand_add_activity"] = True
        with st.form("add_activity_form", clear_on_submit=True):
            st.markdown("<div class='form-title'>🗓️ New Activity</div>", unsafe_allow_html=True)

            r1c1, r1c2 = st.columns(2)
            with r1c1:
                title = st.text_input("Title *", placeholder="e.g. Visit Senso-ji Temple")
                cat_label = st.selectbox("Category", list(ACTIVITY_CATEGORIES.keys()))
            with r1c2:
                slot_label  = st.selectbox("Time Slot", TIME_SLOTS)
                start_time  = st.text_input("Start Time", value="09:00", placeholder="HH:MM")

            r2c1, r2c2, r2c3 = st.columns(3)
            with r2c1:
                duration = st.number_input("Duration (min)", min_value=15, max_value=720, value=60, step=15)
            with r2c2:
                cost = st.number_input("Cost", min_value=0.0, value=0.0, step=5.0)
            with r2c3:
                location = st.text_input("Location / Address", placeholder="e.g. Asakusa, Tokyo")

            r3c1, r3c2 = st.columns(2)
            with r3c1:
                lat = st.number_input("Latitude (optional)", value=0.0, format="%.6f")
            with r3c2:
                lon = st.number_input("Longitude (optional)", value=0.0, format="%.6f")

            notes       = st.text_area("Notes", placeholder="Tips, reminders, booking info…", height=70)
            booking_ref = st.text_input("Booking Reference", placeholder="e.g. ABC123")

            if st.form_submit_button("➕ Add to Itinerary", type="primary", use_container_width=True):
                if not title.strip():
                    st.error("Title is required.")
                else:
                    activity = {
                        "title": title.strip(),
                        "category": ACTIVITY_CATEGORIES[cat_label],
                        "time_slot": SLOT_MAP[slot_label],
                        "start_time": start_time.strip(),
                        "duration": duration,
                        "location": location.strip(),
                        "lat": lat if lat != 0.0 else None,
                        "lon": lon if lon != 0.0 else None,
                        "cost": cost,
                        "notes": notes.strip(),
                        "booking_ref": booking_ref.strip(),
                    }
                    storage.add_activity(trip_id, chosen_str, activity)
                    st.session_state["expand_add_activity"] = False
                    st.success("✅ Activity added!")
                    st.rerun()

    # ── Timeline ────────────────────────────────────────────────────
    # Group by slot
    slots_order = ["morning", "afternoon", "evening", "night"]
    slot_labels_map = {"morning": "🌅 Morning", "afternoon": "☀️ Afternoon", "evening": "🌆 Evening", "night": "🌙 Night"}

    grouped: dict = {s: [] for s in slots_order}
    for act in day_activities:
        slot = act.get("time_slot", "morning")
        if slot not in grouped:
            slot = "morning"
        grouped[slot].append(act)

    if not day_activities:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-title">Nothing planned yet</div>
            <div class="empty-subtitle">Use the form above to add activities for this day.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for slot in slots_order:
            acts = grouped[slot]
            if not acts:
                continue

            st.markdown(f"<div class='slot-header'>{slot_labels_map[slot]} &nbsp;·&nbsp; {len(acts)} {'activity' if len(acts)==1 else 'activities'}</div>", unsafe_allow_html=True)

            for act in sorted(acts, key=lambda a: a.get("start_time","00:00")):
                cat = act.get("category", "activity")
                icon = ACTIVITY_ICONS.get(cat, "📌")
                cost_str = format_currency(act.get("cost",0), currency) if act.get("cost",0) > 0 else "Free"
                dur = act.get("duration", 0)
                dur_str = f"{dur}min" if dur < 60 else f"{dur//60}h{dur%60:02d}m" if dur % 60 else f"{dur//60}h"

                meta_parts = []
                if act.get("start_time"):
                    meta_parts.append(f"🕐 {act['start_time']}")
                if dur:
                    meta_parts.append(f"⏱️ {dur_str}")
                if act.get("location"):
                    meta_parts.append(f"📍 {act['location']}")
                if act.get("booking_ref"):
                    meta_parts.append(f"🎫 {act['booking_ref']}")

                col_card, col_del = st.columns([6, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="activity-card {cat}">
                        <div class="activity-icon">{icon}</div>
                        <div class="activity-info">
                            <div class="activity-title">{act['title']}</div>
                            <div class="activity-meta">{'&nbsp;&nbsp;'.join(meta_parts)}</div>
                            {'<div class="activity-notes">' + act["notes"] + '</div>' if act.get("notes") else ''}
                        </div>
                        <div class="activity-cost">{cost_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑", key=f"del_act_{act['id']}", help="Delete activity"):
                        storage.delete_activity(trip_id, chosen_str, act["id"])
                        st.rerun()

    # ── Day summary ─────────────────────────────────────────────────
    if day_activities:
        st.markdown("<hr>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Total Activities", len(day_activities))
        with s2:
            total_dur = sum(a.get("duration",0) for a in day_activities)
            h, m = divmod(total_dur, 60)
            st.metric("Total Time", f"{h}h {m:02d}m")
        with s3:
            st.metric("Day Budget", format_currency(total_cost, currency))
