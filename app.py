
import streamlit as st
import pandas as pd
from datetime import datetime

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

# --- LOAD DATA ---
@st.cache_data
def load_data():
    return pd.read_csv("courses.csv")

df = load_data()

if "change_log" not in st.session_state:
    st.session_state.change_log = pd.DataFrame(columns=[
        "Course Code", "Old Title", "New Title", "Old Attributes", "New Attributes",
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
            selected = st.selectbox("Select Course to Edit", df["Course Code"])
            course_row = df[df["Course Code"] == selected].iloc[0]

            new_title = st.text_input("New Title", course_row["Course Title"])
            new_attrs = st.text_input("New Attributes", course_row["Attributes"])
            comment = st.text_area("Comment on Change")

            if st.form_submit_button("Submit Edit"):
                idx = df[df["Course Code"] == selected].index[0]

                log_entry = {
                    "Course Code": selected,
                    "Old Title": df.at[idx, "Course Title"],
                    "New Title": new_title,
                    "Old Attributes": df.at[idx, "Attributes"],
                    "New Attributes": new_attrs,
                    "Comment": comment,
                    "Submitted By": "Admin",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sent to ASO": False
                }

                df.at[idx, "Course Title"] = new_title
                df.at[idx, "Attributes"] = new_attrs
                st.session_state.change_log = pd.concat([
                    st.session_state.change_log, pd.DataFrame([log_entry])
                ], ignore_index=True)
                st.success("Edit submitted and logged.")

    st.subheader("Advisor: Submit an Attribute Inquiry")
    with st.form("advisor_form"):
        advisor_name = st.text_input("Your Name")
        advisor_course = st.selectbox("Course", df["Course Code"])
        advisor_comment = st.text_area("Your question or comment")
        if st.form_submit_button("Submit Inquiry"):
            log_entry = {
                "Course Code": advisor_course,
                "Old Title": df[df["Course Code"] == advisor_course]["Course Title"].values[0],
                "New Title": "-",
                "Old Attributes": df[df["Course Code"] == advisor_course]["Attributes"].values[0],
                "New Attributes": "-",
                "Comment": advisor_comment,
                "Submitted By": advisor_name,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Sent to ASO": False
            }
            st.session_state.change_log = pd.concat([
                st.session_state.change_log, pd.DataFrame([log_entry])
            ], ignore_index=True)
            st.success("Inquiry submitted.")

# --- TAB 2: CHANGE LOG ---
with tab2:
    st.header("Change & Inquiry Log")
    if not st.session_state.change_log.empty:
        df_log = st.session_state.change_log.copy()
        for i in df_log.index:
            col1, col2 = st.columns([4, 2])
            with col1:
                df_log.at[i, "Comment"] = st.text_input("Comment", value=df_log.at[i, "Comment"], key=f"log_comment_{i}")
            with col2:
                df_log.at[i, "Sent to ASO"] = st.checkbox("Sent to ASO?", value=df_log.at[i, "Sent to ASO"], key=f"log_check_{i}")

        if is_admin and st.button("Save Log Changes"):
            st.session_state.change_log = df_log
            st.success("Changes saved.")

        st.dataframe(df_log, use_container_width=True)
    else:
        st.info("No changes or inquiries logged yet.")
