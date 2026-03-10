import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.helpers import (
    get_all_trip_dates, format_date,
    MAP_LOCATION_CATEGORIES, MAP_MARKER_COLORS,
)

DAY_PALETTE = [
    "#e8a030", "#4a8cf0", "#10c97a", "#9b6cf8", "#f04a4a",
    "#00d4aa", "#f472b6", "#60a5fa", "#a78bfa", "#fbbf24",
    "#34d399", "#fb7185", "#38bdf8", "#c084fc", "#4ade80",
]


def _no_trip():
    st.markdown('<div class="info-banner">ℹ️ Select a trip from the sidebar to view its map.</div>', unsafe_allow_html=True)


def show_map(storage):
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🗺️ Trip Map</h1>
        <p class="page-subtitle">Pin locations, visualize your route, and explore your destination.</p>
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

    dates     = get_all_trip_dates(trip)
    locations = trip.get("map_locations", [])

    # ── Controls row ────────────────────────────────────────────────
    cc1, cc2, cc3 = st.columns([2, 2, 1])
    with cc1:
        day_filter_opts = ["All Days"] + [d.strftime("%a, %b %d") for d in dates]
        day_filter      = st.selectbox("Filter by Day", day_filter_opts, label_visibility="visible")

    with cc2:
        cat_filter_opts = ["All Categories"] + list(MAP_LOCATION_CATEGORIES.keys())
        cat_filter      = st.selectbox("Filter by Category", cat_filter_opts, label_visibility="visible")

    with cc3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Locations", len(locations))

    # Determine filtered locations
    filtered = locations
    if day_filter != "All Days":
        chosen_date_str = str(dates[day_filter_opts.index(day_filter) - 1])
        filtered = [l for l in locations if l.get("day") == chosen_date_str]
    if cat_filter != "All Categories":
        cat_val = MAP_LOCATION_CATEGORIES[cat_filter]
        filtered = [l for l in filtered if l.get("category") == cat_val]

    # ── Map ─────────────────────────────────────────────────────────
    # Determine center
    if filtered:
        center_lat = sum(l["lat"] for l in filtered) / len(filtered)
        center_lon = sum(l["lon"] for l in filtered) / len(filtered)
        zoom = 12
    elif locations:
        center_lat = sum(l["lat"] for l in locations) / len(locations)
        center_lon = sum(l["lon"] for l in locations) / len(locations)
        zoom = 10
    else:
        center_lat, center_lon, zoom = 35.6762, 139.6503, 5

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap",
        prefer_canvas=True,
    )

    # Day → color map
    date_strs = [str(d) for d in dates]
    day_color_map = {ds: DAY_PALETTE[i % len(DAY_PALETTE)] for i, ds in enumerate(date_strs)}

    for loc in filtered:
        if loc.get("lat") is None or loc.get("lon") is None:
            continue
        day_str = loc.get("day", "")
        cat_val = loc.get("category", "other")
        color   = MAP_MARKER_COLORS.get(cat_val, "#9b6cf8")

        popup_html = f"""
        <div style="font-family:sans-serif;min-width:150px;">
            <b style="font-size:13px;">{loc['name']}</b><br>
            <span style="color:#666;font-size:11px;">{cat_val.title()}</span><br>
            {('<span style="color:#666;font-size:11px;">📅 ' + format_date(day_str) + '</span><br>') if day_str else ''}
            {('<span style="font-size:11px;">' + loc['notes'] + '</span>') if loc.get('notes') else ''}
        </div>
        """
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=loc["name"],
        ).add_to(m)

        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=loc["name"],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;color:white;background:{color};border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4);font-weight:700;">{locations.index(loc)+1}</div>',
                icon_size=(20, 20),
                icon_anchor=(10, 10),
            ),
        ).add_to(m)

    # Connect same-day locations with polyline
    for date_str in date_strs:
        day_locs = [l for l in filtered if l.get("day") == date_str and l.get("lat") and l.get("lon")]
        if len(day_locs) >= 2:
            coords = [[l["lat"], l["lon"]] for l in day_locs]
            color  = day_color_map.get(date_str, "#e8a030")
            folium.PolyLine(coords, color=color, weight=2, opacity=0.5, dash_array="6").add_to(m)

    st_folium(m, use_container_width=True, height=480, returned_objects=[])

    # ── Add Location Form ────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("<h3 class='section-title'>📌 Add Location</h3>", unsafe_allow_html=True)
        with st.form("add_loc_form", clear_on_submit=True):
            loc_name = st.text_input("Place Name *", placeholder="e.g. Senso-ji Temple")
            lc1, lc2 = st.columns(2)
            with lc1:
                lat = st.number_input("Latitude *", value=35.6762, format="%.6f")
            with lc2:
                lon = st.number_input("Longitude *", value=139.6503, format="%.6f")

            lc3, lc4 = st.columns(2)
            with lc3:
                cat_label = st.selectbox("Category", list(MAP_LOCATION_CATEGORIES.keys()))
            with lc4:
                if dates:
                    day_opts   = ["No specific day"] + [d.strftime("%a, %b %d") for d in dates]
                    day_choice = st.selectbox("Day", day_opts)
                    if day_choice == "No specific day":
                        day_str = ""
                    else:
                        day_str = str(dates[day_opts.index(day_choice) - 1])
                else:
                    day_str = ""
                    st.caption("No dates set on trip.")

            notes = st.text_input("Notes", placeholder="Optional tips or info")

            if st.form_submit_button("📌 Add to Map", type="primary", use_container_width=True):
                if not loc_name.strip():
                    st.error("Place name is required.")
                else:
                    storage.add_map_location(trip_id, {
                        "name": loc_name.strip(),
                        "lat": lat,
                        "lon": lon,
                        "category": MAP_LOCATION_CATEGORIES[cat_label],
                        "day": day_str,
                        "notes": notes.strip(),
                    })
                    st.success("📍 Location pinned!")
                    st.rerun()

        st.markdown("""
        <div class="info-banner" style="margin-top:0.75rem;">
            💡 Tip: Use <a href="https://www.latlong.net" target="_blank" style="color:#4a8cf0;">latlong.net</a>
            or Google Maps to find coordinates — right-click any spot and copy the lat/lon.
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("<h3 class='section-title'>📍 Location List</h3>", unsafe_allow_html=True)
        if not locations:
            st.markdown('<p style="color:#4a5568;font-size:0.85rem;">No locations pinned yet.</p>', unsafe_allow_html=True)
        else:
            for i, loc in enumerate(locations):
                col = MAP_MARKER_COLORS.get(loc.get("category","other"), "#9b6cf8")
                day_label = format_date(loc.get("day","")) if loc.get("day") else "All days"
                lc, ld = st.columns([5, 1])
                with lc:
                    st.markdown(f"""
                    <div class="loc-item">
                        <div class="loc-dot" style="background:{col};"></div>
                        <div style="flex:1;">
                            <div class="loc-name">{i+1}. {loc['name']}</div>
                            <div class="loc-meta">{loc.get('category','').title()} · {day_label} · {loc['lat']:.4f}, {loc['lon']:.4f}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with ld:
                    if st.button("🗑", key=f"del_loc_{loc['id']}", help="Remove"):
                        storage.delete_map_location(trip_id, loc["id"])
                        st.rerun()
