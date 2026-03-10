import streamlit as st
from utils.helpers import (
    format_date, format_date_range, get_trip_days, format_currency,
    get_trip_status, get_status_color, get_all_trip_dates,
    ACTIVITY_ICONS, SLOT_EMOJI,
)


def _no_trip():
    st.markdown('<div class="info-banner">ℹ️ Select a trip from the sidebar to generate an export.</div>', unsafe_allow_html=True)


def generate_pdf(trip: dict) -> bytes:
    try:
        from fpdf import FPDF

        currency = trip.get("currency", "USD")
        days_list = get_all_trip_dates(trip)
        expenses  = trip.get("expenses", [])
        accs      = trip.get("accommodations", [])
        packing   = trip.get("packing_list", [])
        itinerary = trip.get("itinerary", {})

        total_spent = sum(e.get("amount", 0) for e in expenses) + sum(a.get("total_cost", 0) for a in accs)
        remaining   = trip.get("budget", 0) - total_spent

        class VoyagerPDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 8)
                self.set_text_color(120, 120, 140)
                self.cell(0, 8, f"Voyager Trip Planner  ·  {trip['name']}", align="R")
                self.ln(2)
                self.set_draw_color(40, 50, 80)
                self.line(10, self.get_y(), 200, self.get_y())
                self.ln(4)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "", 8)
                self.set_text_color(120, 120, 140)
                self.cell(0, 10, f"Page {self.page_no()}", align="C")

        pdf = VoyagerPDF()
        pdf.set_margins(14, 14, 14)
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        # ── Cover Section ────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_text_color(240, 160, 48)
        pdf.cell(0, 14, trip.get("cover_emoji", "") + "  " + trip.get("name", "My Trip"),
                 new_x="LMARGIN", new_y="NEXT", align="L")

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(180, 190, 210)
        pdf.cell(0, 7, trip.get("destination", ""),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Trip overview box
        pdf.set_fill_color(20, 24, 40)
        pdf.set_draw_color(30, 40, 70)
        pdf.rect(14, pdf.get_y(), 182, 28, "DF")

        y0 = pdf.get_y() + 5
        col_w = 45
        overview = [
            ("Dates",      format_date_range(trip.get("start_date",""), trip.get("end_date",""))),
            ("Duration",   f"{get_trip_days(trip.get('start_date',''), trip.get('end_date',''))} days"),
            ("Travelers",  str(trip.get("travelers", 1))),
            ("Trip Type",  trip.get("trip_type", "—")),
        ]
        for i, (label, value) in enumerate(overview):
            x = 16 + i * col_w
            pdf.set_xy(x, y0)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(150, 160, 190)
            pdf.cell(col_w - 2, 4, label.upper())
            pdf.set_xy(x, y0 + 5)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(240, 242, 252)
            pdf.cell(col_w - 2, 5, value)
        pdf.ln(32)

        # ── Budget Summary ────────────────────────────────────────────
        def section_title(title: str):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(240, 160, 48)
            pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(240, 160, 48)
            pdf.line(14, pdf.get_y(), 100, pdf.get_y())
            pdf.ln(4)

        def body_text(txt: str, color=(180, 190, 210), size=9):
            pdf.set_font("Helvetica", "", size)
            pdf.set_text_color(*color)
            pdf.multi_cell(0, 5, txt)

        section_title("Budget Summary")
        budget_lines = [
            ("Total Budget",  format_currency(trip.get("budget", 0), currency)),
            ("Total Spent",   format_currency(total_spent, currency)),
            ("Remaining",     format_currency(remaining, currency)),
            ("Per Person",    format_currency(total_spent / max(trip.get("travelers",1),1), currency)),
        ]
        for label, val in budget_lines:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(180, 190, 210)
            pdf.cell(60, 6, label)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(240, 242, 252)
            pdf.cell(0, 6, val, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Expense by category
        if expenses or accs:
            cat_totals: dict = {}
            for e in expenses:
                cat = e.get("category", "Misc")
                cat_totals[cat] = cat_totals.get(cat, 0) + e.get("amount", 0)
            for a in accs:
                cat_totals["Hotels"] = cat_totals.get("Hotels", 0) + a.get("total_cost", 0)
            for cat, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(150, 160, 190)
                pdf.cell(70, 5, f"  {cat}")
                pdf.set_text_color(200, 210, 230)
                pdf.cell(0, 5, format_currency(amt, currency), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # ── Accommodations ────────────────────────────────────────────
        if accs:
            section_title("Accommodations")
            for acc in accs:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(240, 242, 252)
                pdf.cell(0, 6, acc.get("name", "—"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(150, 160, 190)
                ci  = format_date(acc.get("check_in",""))
                co  = format_date(acc.get("check_out",""))
                nts = acc.get("nights", 0)
                tot = format_currency(acc.get("total_cost",0), currency)
                pdf.cell(0, 5, f"  {ci} → {co}  ·  {nts} nights  ·  {tot}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            pdf.ln(2)

        # ── Day-by-Day Itinerary ──────────────────────────────────────
        section_title("Day-by-Day Itinerary")

        slots_order = ["morning", "afternoon", "evening", "night"]
        slot_labels = {"morning": "Morning", "afternoon": "Afternoon", "evening": "Evening", "night": "Night"}

        for d in days_list:
            ds = str(d)
            day_acts = itinerary.get(ds, [])

            # Day header
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(74, 140, 240)
            pdf.cell(0, 7, f"Day {days_list.index(d)+1}  ·  {d.strftime('%A, %B %d, %Y')}",
                     new_x="LMARGIN", new_y="NEXT")

            if not day_acts:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(100, 110, 140)
                pdf.cell(0, 5, "  No activities planned.", new_x="LMARGIN", new_y="NEXT")
            else:
                grouped: dict = {s: [] for s in slots_order}
                for act in day_acts:
                    slot = act.get("time_slot", "morning")
                    grouped.setdefault(slot, []).append(act)

                for slot in slots_order:
                    acts = grouped.get(slot, [])
                    if not acts:
                        continue
                    pdf.set_font("Helvetica", "B", 8)
                    pdf.set_text_color(120, 130, 160)
                    pdf.cell(0, 5, f"  {slot_labels[slot].upper()}", new_x="LMARGIN", new_y="NEXT")

                    for act in sorted(acts, key=lambda a: a.get("start_time", "00:00")):
                        title = act.get("title", "")
                        time  = act.get("start_time", "")
                        loc   = act.get("location", "")
                        cost  = act.get("cost", 0)
                        notes = act.get("notes", "")

                        pdf.set_font("Helvetica", "B", 9)
                        pdf.set_text_color(220, 225, 245)
                        time_prefix = f"{time}  " if time else ""
                        pdf.cell(0, 5, f"    {time_prefix}{title}", new_x="LMARGIN", new_y="NEXT")

                        if loc or cost:
                            parts = []
                            if loc:   parts.append(f"📍 {loc}")
                            if cost:  parts.append(f"💰 {format_currency(cost, currency)}")
                            pdf.set_font("Helvetica", "", 8)
                            pdf.set_text_color(130, 145, 175)
                            pdf.cell(0, 4, "      " + "  ·  ".join(parts), new_x="LMARGIN", new_y="NEXT")
                        if notes:
                            pdf.set_font("Helvetica", "I", 7)
                            pdf.set_text_color(110, 120, 150)
                            pdf.multi_cell(0, 4, "      " + notes)
            pdf.ln(3)

        # ── Packing List ─────────────────────────────────────────────
        if packing:
            if pdf.get_y() > 220:
                pdf.add_page()
            section_title("Packing List")

            grouped_pack: dict = {}
            for item in packing:
                cat = item.get("category", "Gear")
                grouped_pack.setdefault(cat, []).append(item)

            for cat, items in sorted(grouped_pack.items()):
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(150, 160, 190)
                pdf.cell(0, 5, cat.upper(), new_x="LMARGIN", new_y="NEXT")

                item_cols = 3
                for idx in range(0, len(items), item_cols):
                    row = items[idx: idx + item_cols]
                    for item in row:
                        status = "☑" if item.get("packed") else "☐"
                        pdf.set_font("Helvetica", "", 8)
                        pdf.set_text_color(200, 210, 230)
                        pdf.cell(60, 4.5, f"  {status} {item['item']}")
                    pdf.ln(4.5)
                pdf.ln(2)

        # ── Notes ────────────────────────────────────────────────────
        if trip.get("description"):
            if pdf.get_y() > 230:
                pdf.add_page()
            section_title("Trip Notes")
            body_text(trip["description"])

        return bytes(pdf.output())

    except ImportError:
        return None


def show_export(storage):
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📄 Export Trip</h1>
        <p class="page-subtitle">Generate a beautiful PDF summary of your entire trip.</p>
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

    currency  = trip.get("currency", "USD")
    expenses  = trip.get("expenses", [])
    accs      = trip.get("accommodations", [])
    packing   = trip.get("packing_list", [])
    itinerary = trip.get("itinerary", {})
    total_acts = sum(len(v) for v in itinerary.values())
    total_spent = sum(e.get("amount",0) for e in expenses) + sum(a.get("total_cost",0) for a in accs)
    days = get_trip_days(trip.get("start_date",""), trip.get("end_date",""))
    status = get_trip_status(trip)
    sc = get_status_color(status)

    # Preview Card
    st.markdown(f"""
    <div class="export-card">
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:1rem;">
            <div style="font-size:3rem;">{trip.get("cover_emoji","✈️")}</div>
            <div>
                <div style="font-family:'Sora',sans-serif;font-size:1.4rem;font-weight:700;color:#edf0fc;letter-spacing:-0.02em;">{trip["name"]}</div>
                <div style="color:#e8a030;font-size:0.85rem;margin-top:2px;">📍 {trip.get("destination","—")}</div>
            </div>
            <div style="margin-left:auto;">
                <span class="status-badge" style="background:{sc}20;color:{sc};border:1px solid {sc}40;">{status}</span>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
            <div>
                <div class="export-section-title">DATES</div>
                <div style="font-size:0.85rem;color:#edf0fc;">{format_date_range(trip.get("start_date",""), trip.get("end_date",""))}</div>
            </div>
            <div>
                <div class="export-section-title">DURATION</div>
                <div style="font-size:0.85rem;color:#edf0fc;">{days} days</div>
            </div>
            <div>
                <div class="export-section-title">TRAVELERS</div>
                <div style="font-size:0.85rem;color:#edf0fc;">{trip.get("travelers",1)} people</div>
            </div>
            <div>
                <div class="export-section-title">TRIP TYPE</div>
                <div style="font-size:0.85rem;color:#edf0fc;">{trip.get("trip_type","—")}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Content summary
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<div class="export-card">""", unsafe_allow_html=True)
        st.markdown("<div class='export-section-title'>📅 ITINERARY</div>", unsafe_allow_html=True)
        if itinerary:
            for ds, acts in sorted(itinerary.items()):
                if acts:
                    from utils.helpers import parse_date
                    d = parse_date(ds)
                    day_label = d.strftime("%a, %b %d") if d else ds
                    st.markdown(f"<p style='font-size:0.8rem;color:#7c88a8;margin:2px 0;'>📆 {day_label} — {len(acts)} activities</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:0.8rem;color:#4a5568;'>No itinerary planned yet.</p>", unsafe_allow_html=True)

        st.markdown("<div class='export-section-title' style='margin-top:1rem;'>🏨 ACCOMMODATIONS</div>", unsafe_allow_html=True)
        if accs:
            for acc in accs:
                st.markdown(f"<p style='font-size:0.8rem;color:#7c88a8;margin:2px 0;'>🏨 {acc['name']} ({acc.get('nights',0)} nights)</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:0.8rem;color:#4a5568;'>None added.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""<div class="export-card">""", unsafe_allow_html=True)
        st.markdown("<div class='export-section-title'>💰 BUDGET</div>", unsafe_allow_html=True)
        blines = [
            ("Total Budget",  format_currency(trip.get("budget",0), currency)),
            ("Total Spent",   format_currency(total_spent, currency)),
            ("Remaining",     format_currency(trip.get("budget",0)-total_spent, currency)),
        ]
        for label, val in blines:
            st.markdown(f"<div style='display:flex;justify-content:space-between;font-size:0.82rem;color:#7c88a8;margin:4px 0;'><span>{label}</span><span style='color:#edf0fc;font-weight:600;'>{val}</span></div>", unsafe_allow_html=True)

        st.markdown("<div class='export-section-title' style='margin-top:1rem;'>🎒 PACKING</div>", unsafe_allow_html=True)
        pk_total  = len(packing)
        pk_packed = sum(1 for i in packing if i.get("packed"))
        pk_pct    = (pk_packed / pk_total * 100) if pk_total else 0
        st.markdown(f"<p style='font-size:0.82rem;color:#7c88a8;'>{pk_packed}/{pk_total} items packed ({pk_pct:.0f}%)</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Generate PDF
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>📥 Download</h3>", unsafe_allow_html=True)

    gc1, gc2 = st.columns([2, 1])
    with gc1:
        st.markdown("""
        <div class="info-banner">
            📄 The exported PDF includes: trip overview, day-by-day itinerary, budget summary,
            accommodation details, expense log, and your packing checklist.
        </div>
        """, unsafe_allow_html=True)

    with gc2:
        if st.button("🔄 Generate PDF", type="primary", use_container_width=True):
            with st.spinner("Building your PDF…"):
                pdf_bytes = generate_pdf(trip)
            if pdf_bytes:
                safe_name = trip["name"].replace(" ", "_").replace("/","_")
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{safe_name}_itinerary.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            else:
                st.error("PDF generation failed. Make sure `fpdf2` is installed (`pip install fpdf2`).")
