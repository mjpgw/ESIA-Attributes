import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

st.set_page_config(page_title="Course Attribute Tracker", layout="wide")

# --- USER PERMISSION SETUP ---
AUTHORIZED_USERS = {"Esia1957"}  # Add more passwords here if needed
is_admin = False

# --- PASSWORD PROTECTION ---
with st.sidebar:
    st.markdown("### Admin Access")
    password = st.text_input("Enter password:", type="password")
    if password in AUTHORIZED_USERS:
        is_admin = True
        st.success("Admin access granted")
    elif password:
        st.error("Incorrect password")

# --- GOOGLE SHEETS SETUP ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(
    st.secrets["GOOGLE_CREDENTIALS"], scopes=scope
)
client = gspread.authorize(credentials)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1o8GFr4Wih4QM17KrMzQ2LYsMNmjR1EHtMn4Zvm_s3S8/edit")
data_ws = sheet.worksheet("Courses")
log_ws = sheet.worksheet("Log")

def load_data():
    df = pd.DataFrame(data_ws.get_all_records())
    df.columns = df.columns.str.strip()
    return df

def load_log():
    log_df = pd.DataFrame(log_ws.get_all_records())
    log_df.columns = [str(col).strip() for col in log_df.columns]
    return log_df

def save_log(log_df):
    log_ws.clear()
    log_ws.update([log_df.columns.values.tolist()] + log_df.values.tolist())

df = load_data()
log_df = load_log() if not log_ws.get_all_values() == [] else pd.DataFrame(columns=[
    "Course", "Old Title", "New Title", "Old Attributes", "New Attributes",
    "Comment", "Submitted By", "Timestamp", "Sent to ASO"
])

# --- TABS ---
tab1, tab2 = st.tabs(["📄 Course Table", "🕓 Change Log"])

# --- TAB 1: COURSE TABLE ---
with tab1:
    st.header("Course List")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    if is_admin:
        st.subheader("Admin: Edit Course")
        with st.form("edit_form"):
            selected = st.selectbox("Select Course to Edit", df["Course"])
            course_row = df[df["Course"] == selected].iloc[0]

            new_title = st.text_input("New Title", course_row["Course"])
            new_attrs = st.text_input("New Attributes", course_row["Attribute(s)"])
            comment = st.text_area("Comment on Change")

            submitted = st.form_submit_button("Submit Edit")
            if submitted:
                idx = df[df["Course"] == selected].index[0]

                log_entry = {
                    "Course": selected,
                    "Old Title": df.at[idx, "Course"],
                    "New Title": new_title,
                    "Old Attributes": df.at[idx, "Attribute(s)"],
                    "New Attributes": new_attrs,
                    "Comment": comment,
                    "Submitted By": "Admin",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sent to ASO": False
                }

                df.at[idx, "Course"] = new_title
                df.at[idx, "Attribute(s)"] = new_attrs
                data_ws.update([df.columns.values.tolist()] + df.values.tolist())

                log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
                save_log(log_df)
                st.success("Edit submitted and logged.")

    st.subheader("Advisor: Submit an Attribute Inquiry")
    with st.form("advisor_form"):
        advisor_name = st.text_input("Your Name")
        advisor_course = st.selectbox("Course", df["Course"])
        advisor_comment = st.text_area("Your question or comment")
        submitted_inquiry = st.form_submit_button("Submit Inquiry")
        if submitted_inquiry:
            log_entry = {
                "Course": advisor_course,
                "Old Title": df[df["Course"] == advisor_course]["Course"].values[0],
                "New Title": "-",
                "Old Attributes": df[df["Course"] == advisor_course]["Attribute(s)"].values[0],
                "New Attributes": "-",
                "Comment": advisor_comment,
                "Submitted By": advisor_name,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Sent to ASO": False
            }
            log_df = pd.concat([log_df, pd.DataFrame([log_entry])], ignore_index=True)
            save_log(log_df)
            st.success("Inquiry submitted.")

# --- TAB 2: CHANGE LOG ---
with tab2:
    st.header("Change & Inquiry Log")
    if not log_df.empty:
        for i in log_df.index:
            col1, col2 = st.columns([4, 2])
            with col1:
                log_df.at[i, "Comment"] = st.text_input("Comment", value=log_df.at[i, "Comment"], key=f"log_comment_{i}")
            with col2:
                log_df.at[i, "Sent to ASO"] = st.checkbox("Sent to ASO?", value=log_df.at[i, "Sent to ASO"], key=f"log_check_{i}")

        if is_admin and st.button("Save Log Changes"):
            save_log(log_df)
            st.success("Changes saved.")

        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No changes or inquiries logged yet.")
