import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import (
    format_currency, format_date,
    EXPENSE_CATEGORIES, EXPENSE_CAT_COLORS, CURRENCIES,
    get_trip_days,
)


def _no_trip():
    st.markdown('<div class="info-banner">ℹ️ Select a trip from the sidebar to track its budget.</div>', unsafe_allow_html=True)


def show_budget(storage):
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">💰 Budget Tracker</h1>
        <p class="page-subtitle">Track every dollar — categories, breakdowns, and spending trends.</p>
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

    currency = trip.get("currency", "USD")
    budget   = trip.get("budget", 0)
    expenses = trip.get("expenses", [])
    accs     = trip.get("accommodations", [])
    days     = get_trip_days(trip.get("start_date",""), trip.get("end_date",""))
    travelers = trip.get("travelers", 1)

    total_spent = sum(e.get("amount",0) for e in expenses)
    acc_cost    = sum(a.get("total_cost",0) for a in accs)
    grand_spent = total_spent + acc_cost
    remaining   = budget - grand_spent
    pct_used    = (grand_spent / budget * 100) if budget > 0 else 0
    bar_color   = "#f04a4a" if pct_used > 90 else "#e8a030" if pct_used > 70 else "#10c97a"

    # ── Overview KPIs ───────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Total Budget",  format_currency(budget, currency))
    with c2: st.metric("Total Spent",   format_currency(grand_spent, currency))
    with c3: st.metric("Remaining",     format_currency(remaining, currency))
    with c4: st.metric("Per Person",    format_currency(grand_spent / travelers, currency) if travelers else "—")
    with c5: st.metric("Per Day",       format_currency(grand_spent / days, currency) if days else "—")

    # Progress bar
    st.markdown(f"""
    <div style="margin:1rem 0 1.5rem 0;">
        <div class="progress-header">
            <span class="progress-label">Budget Used</span>
            <span class="progress-value">{pct_used:.1f}%  ({format_currency(grand_spent, currency)} / {format_currency(budget, currency)})</span>
        </div>
        <div class="progress-track" style="height:12px;">
            <div class="progress-fill" style="width:{min(pct_used,100):.1f}%;background:{bar_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if pct_used > 100:
        st.markdown(f'<div class="warning-banner">⚠️ You are {format_currency(abs(remaining), currency)} over budget!</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown("<h3 class='section-title'>📊 Spending by Category</h3>", unsafe_allow_html=True)

        # Aggregate by category
        cat_totals: dict = {}
        for e in expenses:
            cat = e.get("category", "💳 Misc")
            cat_totals[cat] = cat_totals.get(cat, 0) + e.get("amount", 0)
        if acc_cost > 0:
            cat_totals["🏨 Hotels"] = cat_totals.get("🏨 Hotels", 0) + acc_cost

        if cat_totals:
            colors = [EXPENSE_CAT_COLORS.get(c, "#6b7280") for c in cat_totals.keys()]
            fig = go.Figure(data=[go.Pie(
                labels=list(cat_totals.keys()),
                values=list(cat_totals.values()),
                hole=0.55,
                marker=dict(colors=colors),
                textfont=dict(size=11, color="#edf0fc"),
                hovertemplate="<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>",
            )])
            fig.update_layout(
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8892a8", family="DM Sans"),
                margin=dict(t=10, b=10, l=0, r=0),
                height=260,
                legend=dict(orientation="v", font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Bar chart
            fig2 = go.Figure(data=[go.Bar(
                x=list(cat_totals.keys()),
                y=list(cat_totals.values()),
                marker_color=colors,
                marker_line_width=0,
            )])
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8892a8", family="DM Sans"),
                margin=dict(t=10, b=40, l=40, r=10),
                height=200,
                xaxis=dict(showgrid=False, color="#4a5568"),
                yaxis=dict(showgrid=True, gridcolor="#181e30", color="#4a5568"),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="empty-state"><div class="empty-icon">📊</div><div class="empty-title">No expenses yet</div><div class="empty-subtitle">Add your first expense below.</div></div>', unsafe_allow_html=True)

    with right:
        st.markdown("<h3 class='section-title'>💳 Budget Split</h3>", unsafe_allow_html=True)
        # Budget allocation form
        with st.expander("⚙️ Set Category Targets", expanded=False):
            st.caption("Coming soon: set per-category budget targets.")

        # Category summary table
        if cat_totals:
            for cat, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
                col = EXPENSE_CAT_COLORS.get(cat, "#6b7280")
                pct = (amt / grand_spent * 100) if grand_spent > 0 else 0
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div class="progress-header">
                        <span class="progress-label">{cat}</span>
                        <span class="progress-value">{format_currency(amt, currency)}</span>
                    </div>
                    <div class="progress-track" style="height:6px;">
                        <div style="width:{pct:.1f}%;height:100%;border-radius:99px;background:{col};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Tabs: Expenses / Accommodations ──────────────────────────────
    tab_exp, tab_acc = st.tabs(["💳 Expenses", "🏨 Accommodations"])

    with tab_exp:
        # Add Expense
        with st.expander("➕ Log Expense", expanded=False):
            with st.form("add_expense_form", clear_on_submit=True):
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    cat = st.selectbox("Category", EXPENSE_CATEGORIES)
                with ec2:
                    amount = st.number_input("Amount", min_value=0.01, value=50.0, step=5.0)
                with ec3:
                    exp_date = st.date_input("Date", value=None)
                description = st.text_input("Description", placeholder="e.g. Dinner at Nobu, Flight SQ323…")
                if st.form_submit_button("💾 Log Expense", type="primary", use_container_width=True):
                    storage.add_expense(trip_id, {
                        "category": cat,
                        "amount": amount,
                        "description": description.strip(),
                        "date": str(exp_date) if exp_date else "",
                    })
                    st.success("✅ Expense logged!")
                    st.rerun()

        # List
        if not expenses:
            st.markdown('<p style="color:#4a5568;font-size:0.85rem;padding:1rem 0;">No expenses logged yet.</p>', unsafe_allow_html=True)
        else:
            exp_sorted = sorted(expenses, key=lambda e: e.get("date",""), reverse=True)
            for exp in exp_sorted:
                col = EXPENSE_CAT_COLORS.get(exp.get("category",""), "#6b7280")
                date_str = format_date(exp.get("date","")) if exp.get("date") else "—"
                c_item, c_del = st.columns([6, 1])
                with c_item:
                    st.markdown(f"""
                    <div class="expense-item" style="border-left:3px solid {col};">
                        <div class="expense-cat">{exp.get("category","💳").split()[0]}</div>
                        <div class="expense-info">
                            <div class="expense-desc">{exp.get("description","—")}</div>
                            <div class="expense-date">{exp.get("category","")} · {date_str}</div>
                        </div>
                        <div class="expense-amount">{format_currency(exp.get("amount",0), currency)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_del:
                    if st.button("🗑", key=f"del_exp_{exp['id']}", help="Delete"):
                        storage.delete_expense(trip_id, exp["id"])
                        st.rerun()

    with tab_acc:
        # Add Accommodation
        with st.expander("➕ Add Stay", expanded=False):
            with st.form("add_acc_form", clear_on_submit=True):
                ac1, ac2 = st.columns(2)
                with ac1:
                    acc_name = st.text_input("Hotel / Stay Name *", placeholder="e.g. Park Hyatt Tokyo")
                    acc_addr = st.text_input("Address", placeholder="Optional")
                with ac2:
                    from utils.helpers import parse_date
                    ac_in  = st.date_input("Check-in", value=None)
                    ac_out = st.date_input("Check-out", value=None)
                ac3, ac4 = st.columns(2)
                with ac3:
                    cpn = st.number_input("Cost per Night", min_value=0.0, value=150.0, step=10.0)
                with ac4:
                    acc_ref = st.text_input("Booking Ref", placeholder="Optional")
                acc_notes = st.text_input("Notes", placeholder="Optional")
                if st.form_submit_button("💾 Save Stay", type="primary", use_container_width=True):
                    if not acc_name.strip():
                        st.error("Name is required.")
                    else:
                        nights = 0
                        if ac_in and ac_out:
                            nights = max(0, (ac_out - ac_in).days)
                        storage.add_accommodation(trip_id, {
                            "name": acc_name.strip(),
                            "address": acc_addr.strip(),
                            "check_in": str(ac_in) if ac_in else "",
                            "check_out": str(ac_out) if ac_out else "",
                            "cost_per_night": cpn,
                            "total_cost": cpn * nights,
                            "nights": nights,
                            "booking_ref": acc_ref.strip(),
                            "notes": acc_notes.strip(),
                        })
                        st.success("✅ Stay added!")
                        st.rerun()

        # List
        if not accs:
            st.markdown('<p style="color:#4a5568;font-size:0.85rem;padding:1rem 0;">No accommodations added yet.</p>', unsafe_allow_html=True)
        else:
            for acc in accs:
                nights = acc.get("nights", 0)
                total  = acc.get("total_cost", 0)
                cr, cd = st.columns([6, 1])
                with cr:
                    st.markdown(f"""
                    <div class="acc-card">
                        <div class="acc-name">🏨 {acc["name"]}</div>
                        <div class="acc-meta">
                            <span>📅 {format_date(acc.get("check_in",""))} → {format_date(acc.get("check_out",""))}</span>
                            <span>🌙 {nights} nights</span>
                            <span>💰 {format_currency(acc.get("cost_per_night",0), currency)}/night</span>
                            <span>💳 Total: {format_currency(total, currency)}</span>
                            {'<span>🎫 ' + acc["booking_ref"] + '</span>' if acc.get("booking_ref") else ''}
                        </div>
                        {'<div style="font-size:0.78rem;color:#7c88a8;margin-top:4px;">' + acc["notes"] + '</div>' if acc.get("notes") else ''}
                    </div>
                    """, unsafe_allow_html=True)
                with cd:
                    if st.button("🗑", key=f"del_acc_{acc['id']}", help="Delete"):
                        storage.delete_accommodation(trip_id, acc["id"])
                        st.rerun()
