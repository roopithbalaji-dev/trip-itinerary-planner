import streamlit as st
import plotly.graph_objects as go
from utils.helpers import (
    get_trip_status, format_date_range, get_trip_days,
    format_currency, get_status_color, get_days_until,
)


def show_dashboard(storage):
    trips = storage.get_all_trips()

    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">Welcome back, Traveler ✈️</h1>
        <p class="page-subtitle">Your travel command center — plan, track, and explore the world.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ─────────────────────────────────────────────────────
    upcoming = [t for t in trips if get_trip_status(t) == "Upcoming"]
    active   = [t for t in trips if get_trip_status(t) == "Active"]
    completed = [t for t in trips if get_trip_status(t) == "Completed"]
    destinations = len(set(t.get("destination", "") for t in trips if t.get("destination")))
    total_days = sum(get_trip_days(t.get("start_date",""), t.get("end_date","")) for t in trips)

    cols = st.columns(5)
    kpis = [
        ("✈️", str(len(trips)), "Total Trips"),
        ("🔜", str(len(upcoming)), "Upcoming"),
        ("🟢", str(len(active)), "Active"),
        ("✅", str(len(completed)), "Completed"),
        ("📍", str(destinations), "Destinations"),
    ]
    for col, (icon, val, label) in zip(cols, kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main Layout ─────────────────────────────────────────────────
    left, right = st.columns([3, 1], gap="large")

    with left:
        st.markdown("<h3 class='section-title'>🗺️ All Trips</h3>", unsafe_allow_html=True)

        if not trips:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🗺️</div>
                <div class="empty-title">No trips yet</div>
                <div class="empty-subtitle">Head to "My Trips" to create your first adventure!</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("➕ Create Your First Trip", type="primary"):
                st.session_state.page = "trips"
                st.session_state.show_create_form = True
                st.rerun()
        else:
            sorted_trips = sorted(trips, key=lambda t: t.get("start_date", ""), reverse=True)
            for trip in sorted_trips:
                status = get_trip_status(trip)
                sc = get_status_color(status)
                days = get_trip_days(trip.get("start_date",""), trip.get("end_date",""))
                dr = format_date_range(trip.get("start_date",""), trip.get("end_date",""))
                budget = format_currency(trip.get("budget", 0), trip.get("currency", "USD"))
                emoji = trip.get("cover_emoji", "✈️")

                extra = ""
                if status == "Upcoming":
                    dl = get_days_until(trip["start_date"])
                    extra = f"<span class='days-badge'>in {dl} days</span>"
                elif status == "Active":
                    extra = "<span class='active-badge'>● Active</span>"

                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"""
                    <div class="trip-card">
                        <div class="trip-card-left">
                            <div class="trip-emoji">{emoji}</div>
                            <div class="trip-info">
                                <div class="trip-name">{trip["name"]}</div>
                                <div class="trip-destination">📍 {trip.get("destination","—")}</div>
                                <div class="trip-meta">
                                    <span>📅 {dr}</span>
                                    <span>⏱️ {days}d</span>
                                    <span>💰 {budget}</span>
                                    <span>👥 {trip.get("travelers",1)}</span>
                                    <span>🏷️ {trip.get("trip_type","")}</span>
                                </div>
                            </div>
                        </div>
                        <div class="trip-card-right">
                            <span class="status-badge" style="background:{sc}20;color:{sc};border:1px solid {sc}40;">{status}</span>
                            {extra}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Open →", key=f"dash_open_{trip['id']}", use_container_width=True):
                        st.session_state.current_trip_id = trip["id"]
                        st.session_state.page = "itinerary"
                        st.rerun()

    with right:
        # Upcoming trips
        st.markdown("<h3 class='section-title'>⏰ Upcoming</h3>", unsafe_allow_html=True)
        up_sorted = sorted(upcoming, key=lambda t: t.get("start_date", ""))[:4]
        if up_sorted:
            for t in up_sorted:
                dl = get_days_until(t["start_date"])
                st.markdown(f"""
                <div class="upcoming-item">
                    <div class="upcoming-emoji">{t.get("cover_emoji","✈️")}</div>
                    <div class="upcoming-info">
                        <div class="upcoming-name">{t["name"]}</div>
                        <div class="upcoming-date">{t.get("destination","")} • {dl}d away</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#4a5568;font-size:0.82rem;'>No upcoming trips planned.</p>", unsafe_allow_html=True)

        # Trip type pie chart
        if trips:
            st.markdown("<h3 class='section-title' style='margin-top:1.5rem;'>📊 Trip Types</h3>", unsafe_allow_html=True)
            type_counts: dict = {}
            for t in trips:
                tt = t.get("trip_type", "Other")
                type_counts[tt] = type_counts.get(tt, 0) + 1

            palette = ["#e8a030","#4a8cf0","#10c97a","#9b6cf8","#f04a4a","#00d4aa","#f472b6","#60a5fa","#a78bfa"]
            fig = go.Figure(data=[go.Pie(
                labels=list(type_counts.keys()),
                values=list(type_counts.values()),
                hole=0.55,
                marker=dict(colors=palette[:len(type_counts)]),
                textfont=dict(size=11, color="#edf0fc"),
            )])
            fig.update_layout(
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8892a8", family="DM Sans"),
                margin=dict(t=10, b=10, l=0, r=0),
                height=220,
                legend=dict(orientation="v", font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Budget summary
        if trips:
            total_budget = sum(t.get("budget", 0) for t in trips)
            total_spent  = sum(
                sum(e.get("amount", 0) for e in t.get("expenses", []))
                for t in trips
            )
            pct = (total_spent / total_budget * 100) if total_budget > 0 else 0
            bar_color = "#f04a4a" if pct > 90 else "#e8a030" if pct > 70 else "#10c97a"

            st.markdown("<h3 class='section-title' style='margin-top:1.5rem;'>💰 Budget</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="budget-overview">
                <div class="budget-row">
                    <span>Total Budget</span>
                    <span class="budget-total">${total_budget:,.0f}</span>
                </div>
                <div class="budget-row">
                    <span>Logged Spend</span>
                    <span class="budget-spent">${total_spent:,.0f}</span>
                </div>
                <div class="budget-bar-container">
                    <div class="budget-bar" style="width:{min(pct,100):.1f}%;background:{bar_color};"></div>
                </div>
                <div class="budget-pct">{pct:.1f}% of total budget used</div>
            </div>
            """, unsafe_allow_html=True)
