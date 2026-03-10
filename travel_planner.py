import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from datetime import timedelta
from fpdf import FPDF

st.set_page_config(page_title="Travel Planner", layout="wide")

st.title("🌍 Smart Travel Planner")

# ---------------- Sidebar ----------------

st.sidebar.header("Trip Setup")

trip_name = st.sidebar.text_input("Trip Name")

date_range = st.sidebar.date_input(
    "Select Trip Dates",
    value=[]
)

# Calculate days automatically
days = []

if len(date_range) == 2:

    start = date_range[0]
    end = date_range[1]

    days_count = (end - start).days + 1

    days = [start + timedelta(days=i) for i in range(days_count)]

    st.sidebar.success(f"{days_count} Day Trip")

# ---------------- Itinerary ----------------

if "itinerary" not in st.session_state:
    st.session_state.itinerary = {}

if days:

    st.header("📅 Trip Itinerary")

    for i, day in enumerate(days):

        day_label = f"Day {i+1} - {day}"

        if day_label not in st.session_state.itinerary:
            st.session_state.itinerary[day_label] = []

        st.subheader(day_label)

        col1, col2 = st.columns([4,1])

        activity = col1.text_input(
            "Add Activity",
            key=f"activity_{i}"
        )

        if col2.button("Add", key=f"btn_{i}"):

            if activity:
                st.session_state.itinerary[day_label].append(activity)

        for act in st.session_state.itinerary[day_label]:
            st.write("•", act)


# ---------------- Export PDF ----------------

st.header("📄 Export Itinerary")

def create_pdf():

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200,10,txt=f"Trip: {trip_name}", ln=True)

    for day in st.session_state.itinerary:

        pdf.cell(200,10,txt=day, ln=True)

        for act in st.session_state.itinerary[day]:
            pdf.cell(200,10,txt=f"- {act}", ln=True)

    file = "itinerary.pdf"
    pdf.output(file)

    return file

if st.button("Generate PDF"):

    pdf_file = create_pdf()

    with open(pdf_file,"rb") as f:

        st.download_button(
            label="Download Itinerary",
            data=f,
            file_name="trip_itinerary.pdf",
            mime="application/pdf"
        )
