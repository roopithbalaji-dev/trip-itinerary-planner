import streamlit as st
from utils.helpers import PACKING_CATEGORIES, DEFAULT_PACKING


def _no_trip():
    st.markdown('<div class="info-banner">ℹ️ Select a trip from the sidebar to manage its packing list.</div>', unsafe_allow_html=True)


def show_packing(storage):
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">🎒 Packing List</h1>
        <p class="page-subtitle">Never forget a thing — build and track your packing checklist.</p>
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

    packing = trip.get("packing_list", [])
    total   = len(packing)
    packed  = sum(1 for i in packing if i.get("packed"))

    # ── Overview ─────────────────────────────────────────────────────
    oc1, oc2, oc3, oc4 = st.columns(4)
    with oc1: st.metric("Total Items", total)
    with oc2: st.metric("Packed",      packed)
    with oc3: st.metric("Remaining",   total - packed)
    with oc4:
        pct = (packed / total * 100) if total > 0 else 0
        st.metric("Progress", f"{pct:.0f}%")

    if total > 0:
        bar_color = "#10c97a" if pct == 100 else "#e8a030" if pct >= 50 else "#f04a4a"
        st.markdown(f"""
        <div style="margin:0.5rem 0 1.5rem 0;">
            <div class="progress-track" style="height:10px;">
                <div class="progress-fill" style="width:{pct:.0f}%;background:{bar_color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if pct == 100:
            st.markdown('<div class="info-banner" style="background:rgba(16,201,122,0.08);border-color:rgba(16,201,122,0.3);color:#10c97a;">🎉 All packed! You\'re ready to go.</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Layout: left=list, right=add form ───────────────────────────
    left, right = st.columns([3, 2], gap="large")

    with right:
        # Quick-add suggested items
        st.markdown("<h3 class='section-title'>📋 Quick Add Suggestions</h3>", unsafe_allow_html=True)
        existing_names = {i["item"].lower() for i in packing}
        cat_choice = st.selectbox("Category", list(DEFAULT_PACKING.keys()), key="sugg_cat")
        sugg_items  = DEFAULT_PACKING.get(cat_choice, [])
        available   = [(name, essential) for name, essential in sugg_items if name.lower() not in existing_names]

        if not available:
            st.markdown("<p style='color:#4a5568;font-size:0.82rem;'>All suggestions added for this category.</p>", unsafe_allow_html=True)
        else:
            cols = st.columns(2)
            for idx, (name, essential) in enumerate(available):
                with cols[idx % 2]:
                    btn_label = f"{'⭐ ' if essential else ''}{name}"
                    if st.button(btn_label, key=f"sugg_{name}", use_container_width=True):
                        storage.add_packing_item(trip_id, {
                            "item": name,
                            "category": cat_choice,
                            "packed": False,
                            "essential": essential,
                        })
                        st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # Custom item form
        st.markdown("<h3 class='section-title'>➕ Add Custom Item</h3>", unsafe_allow_html=True)
        with st.form("add_pack_form", clear_on_submit=True):
            item_name = st.text_input("Item Name *", placeholder="e.g. Travel umbrella")
            col_cat, col_ess = st.columns(2)
            with col_cat:
                item_cat = st.selectbox("Category", PACKING_CATEGORIES, key="pack_cat")
            with col_ess:
                essential = st.checkbox("Essential?", value=False)
            if st.form_submit_button("➕ Add Item", type="primary", use_container_width=True):
                if not item_name.strip():
                    st.error("Item name is required.")
                else:
                    storage.add_packing_item(trip_id, {
                        "item": item_name.strip(),
                        "category": item_cat,
                        "packed": False,
                        "essential": essential,
                    })
                    st.rerun()

        # Bulk actions
        if packing:
            st.markdown("<hr>", unsafe_allow_html=True)
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("✅ Mark All Packed", use_container_width=True):
                    for item in packing:
                        if not item.get("packed"):
                            storage.toggle_packing_item(trip_id, item["id"])
                    st.rerun()
            with bc2:
                if st.button("🔄 Reset All", use_container_width=True):
                    for item in packing:
                        if item.get("packed"):
                            storage.toggle_packing_item(trip_id, item["id"])
                    st.rerun()

    with left:
        st.markdown("<h3 class='section-title'>🎒 My Packing List</h3>", unsafe_allow_html=True)

        if not packing:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🎒</div>
                <div class="empty-title">Empty packing list</div>
                <div class="empty-subtitle">Use suggestions or the form on the right to add items.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Filter
            fc1, fc2 = st.columns(2)
            with fc1:
                cat_filter = st.selectbox("Filter Category", ["All"] + PACKING_CATEGORIES, key="pack_cat_filter", label_visibility="collapsed")
            with fc2:
                status_filter = st.selectbox("Filter Status", ["All", "Unpacked", "Packed"], key="pack_status_filter", label_visibility="collapsed")

            # Group by category
            grouped: dict = {}
            for item in packing:
                cat = item.get("category", "🎒 Gear")
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(item)

            for cat, items in sorted(grouped.items()):
                if cat_filter != "All" and cat != cat_filter:
                    continue

                cat_total  = len(items)
                cat_packed = sum(1 for i in items if i.get("packed"))
                cat_pct    = cat_packed / cat_total * 100 if cat_total else 0

                st.markdown(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;margin:1rem 0 6px 0;">
                    <span style="font-size:0.75rem;font-weight:600;letter-spacing:0.08em;color:#4a5568;text-transform:uppercase;">{cat}</span>
                    <span style="font-size:0.72rem;color:#7c88a8;">{cat_packed}/{cat_total}</span>
                </div>
                """, unsafe_allow_html=True)

                for item in sorted(items, key=lambda i: (i.get("packed", False), i["item"])):
                    is_packed = item.get("packed", False)
                    if status_filter == "Packed" and not is_packed:
                        continue
                    if status_filter == "Unpacked" and is_packed:
                        continue

                    essential = item.get("essential", False)
                    pi_col, pd_col = st.columns([5, 1])
                    with pi_col:
                        checked = st.checkbox(
                            item["item"],
                            value=is_packed,
                            key=f"pack_cb_{item['id']}",
                        )
                        if checked != is_packed:
                            storage.toggle_packing_item(trip_id, item["id"])
                            st.rerun()
                    with pd_col:
                        if st.button("🗑", key=f"del_pack_{item['id']}", help="Remove"):
                            storage.delete_packing_item(trip_id, item["id"])
                            st.rerun()
