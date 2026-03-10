import streamlit as st
import pandas as pd
import sqlite3
from datetime import timedelta
from fpdf import FPDF

st.set_page_config(page_title="Travel Planner", layout="wide")

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
location TEXT
)
""")

conn.commit()

# ---------------- CREATE TRIP ----------------

st.sidebar.header("Create Trip")

trip_name = st.sidebar.text_input("Trip Name")

date_range = st.sidebar.date_input("Trip Dates", value=[])

if st.sidebar.button("Create Trip"):

    if trip_name and len(date_range) == 2:

        cursor.execute("""
        INSERT INTO trips(trip_name,start_date,end_date)
        VALUES(?,?,?)
        """,(trip_name,str(date_range[0]),str(date_range[1])))

        conn.commit()
        st.rerun()

# ---------------- LOAD TRIPS ----------------

trips = pd.read_sql_query("SELECT * FROM trips", conn)

if trips.empty:
    st.warning("Create a trip first")
    st.stop()

trip_selected = st.sidebar.selectbox("Select Trip", trips["trip_name"])

trip_id = trips[trips["trip_name"]==trip_selected]["id"].values[0]

trip_data = trips[trips["id"]==trip_id].iloc[0]

start = pd.to_datetime(trip_data["start_date"])
end = pd.to_datetime(trip_data["end_date"])

days_count = (end-start).days + 1
days = [start + timedelta(days=i) for i in range(days_count)]

day_labels = [f"Day {i+1} - {d.date()}" for i,d in enumerate(days)]

# ---------------- ADD ACTIVITY ----------------

st.header("Add Activity")

selected_day = st.selectbox("Select Day", day_labels)
with st.form("add_activity_form"):

    activity = st.text_input("Activity")
    location = st.text_input("Location")

    submitted = st.form_submit_button("Add Activity")

    if submitted and activity:

        cursor.execute("""
        INSERT INTO activities(trip_id,day,activity,location)
        VALUES(?,?,?,?)
        """,(trip_id,selected_day,activity,location))

        conn.commit()

        st.success("Activity added")
        st.rerun()


# ---------------- DISPLAY ITINERARY ----------------

st.header("Trip Itinerary")

activities = pd.read_sql_query(
f"SELECT * FROM activities WHERE trip_id={trip_id}",
conn
)

for day in day_labels:

    st.subheader(day)

    day_data = activities[activities["day"]==day]

    if day_data.empty:

        st.write("No activities yet")

    else:

        for _,row in day_data.iterrows():

            col1,col2 = st.columns([8,1])

            col1.write(f"• {row['activity']} ({row['location']})")

            if col2.button("Delete", key=row["id"]):

                cursor.execute(
                "DELETE FROM activities WHERE id=?",
                (row["id"],)
                )

                conn.commit()

                st.rerun()

# ---------------- EXPORT ----------------

st.header("Export Itinerary")

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
