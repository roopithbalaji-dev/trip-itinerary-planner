import streamlit as st
import pandas as pd
import sqlite3
from datetime import timedelta
from fpdf import FPDF
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Smart Travel Planner", layout="wide")

st.title("🌍 Smart Travel Planner")

# ---------------- DATABASE ----------------

conn = sqlite3.connect("travel_planner.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS trips(
id INTEGER PRIMARY KEY,
trip_name TEXT,
start_date TEXT,
end_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS activities(
id INTEGER PRIMARY KEY,
trip_id INTEGER,
day TEXT,
activity TEXT,
location TEXT,
lat REAL,
lon REAL
)
""")

conn.commit()

# ---------------- SIDEBAR ----------------

st.sidebar.header("Trips")

trip_name = st.sidebar.text_input("Trip Name")
date_range = st.sidebar.date_input("Trip Dates", value=[])

if st.sidebar.button("Create Trip"):

    if trip_name and len(date_range) == 2:

        cursor.execute("""
        INSERT INTO trips(trip_name,start_date,end_date)
        VALUES(?,?,?)
        """,(trip_name,str(date_range[0]),str(date_range[1])))

        conn.commit()
        st.sidebar.success("Trip created")
        st.rerun()

# Load trips
trips = pd.read_sql_query("SELECT * FROM trips", conn)

if trips.empty:
    st.warning("Create a trip first")
    st.stop()

trip_selected = st.sidebar.selectbox("Select Trip", trips["trip_name"])

trip_id = trips[trips["trip_name"]==trip_selected]["id"].values[0]

trip_data = trips[trips["id"]==trip_id].iloc[0]

start = pd.to_datetime(trip_data["start_date"])
end = pd.to_datetime(trip_data["end_date"])

days_count = (end - start).days + 1
days = [start + timedelta(days=i) for i in range(days_count)]

# ---------------- ITINERARY ----------------

st.header("📅 Trip Itinerary")

activities = pd.read_sql_query(
f"SELECT * FROM activities WHERE trip_id={trip_id}",
conn
)

for i,day in enumerate(days):

    day_label = f"Day {i+1} - {day.date()}"

    st.subheader(day_label)

    # Show saved activities
    day_data = activities[activities["day"] == day_label]

    if not day_data.empty:

        for _,row in day_data.iterrows():

            col1,col2 = st.columns([6,1])

            col1.write(f"• {row['activity']} ({row['location']})")

            if col2.button("❌", key=f"del{row['id']}"):

                cursor.execute(
                "DELETE FROM activities WHERE id=?",
                (row["id"],)
                )

                conn.commit()
                st.rerun()

    # Add new activity
    col1,col2,col3,col4 = st.columns([3,3,2,1])

    activity = col1.text_input(
        "Activity",
        key=f"act{i}"
    )

    location = col2.text_input(
        "Location",
        key=f"loc{i}"
    )

    coords = col3.text_input(
        "Lat,Lon",
        key=f"coord{i}"
    )

    if col4.button("Add", key=f"add{i}"):

        lat,lon = None,None

        if coords:
            lat,lon = coords.split(",")

        cursor.execute("""
        INSERT INTO activities(trip_id,day,activity,location,lat,lon)
        VALUES(?,?,?,?,?,?)
        """,(trip_id,day_label,activity,location,lat,lon))

        conn.commit()
        st.rerun()

# ---------------- MAP ----------------

st.header("📍 Map")

if not activities.empty:

    m = folium.Map(location=[20,0], zoom_start=2)

    for _,row in activities.iterrows():

        if row["lat"] and row["lon"]:

            folium.Marker(
                location=[row["lat"],row["lon"]],
                popup=row["activity"]
            ).add_to(m)

    st_folium(m,width=900)

# ---------------- EXPORT ----------------

st.header("📄 Export Itinerary")

def create_pdf():

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200,10,txt=f"Trip: {trip_selected}", ln=True)

    for _,row in activities.iterrows():

        pdf.cell(
            200,
            10,
            txt=f"{row['day']} - {row['activity']} ({row['location']})",
            ln=True
        )

    file = "trip_plan.pdf"
    pdf.output(file)

    return file

if st.button("Generate PDF"):

    pdf_file = create_pdf()

    with open(pdf_file,"rb") as f:

        st.download_button(
            "Download Itinerary",
            f,
            "trip_plan.pdf",
            "application/pdf"
        )
