import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

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

# --- GOOGLE SHEETS CONNECTION ---
scope = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(
    st.secrets["GOOGLE_CREDENTIALS"], scopes=scope
)
client = gspread.authorize(credentials)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1o8GFr4Wih4QM17KrMzQ2LYsMNmjR1EHtMn4Zvm_s3S8")
courses_ws = sheet.worksheet("Courses")
change_log_ws = sheet.worksheet("Log")
inquiry_log_ws = sheet.worksheet("Inquiries")

# --- LOAD DATA FUNCTIONS ---
@st.cache_data
def load_courses():
    df = pd.DataFrame(courses_ws.get_all_records())
    df.columns = df.columns.str.strip()
    return df

def load_log(ws):
    df = pd.DataFrame(ws.get_all_records())
    df.columns = [str(col).strip() for col in df.columns]
    return df

courses_df = load_courses()
change_log_df = load_log(change_log_ws) if change_log_ws.get_all_values() else pd.DataFrame(columns=[
    "Course", "Old Title", "New Title", "Old Attributes", "New Attributes",
    "Comment", "Submitted By", "Timestamp", "Sent to ASO"
])
inquiry_log_df = load_log(inquiry_log_ws) if inquiry_log_ws.get_all_values() else pd.DataFrame(columns=[
    "Name", "Comment", "Addressed?", "Timestamp"
])

# Ensure checkbox columns are properly typed and defaulted to False
if "Sent to ASO" in change_log_df.columns:
    change_log_df["Sent to ASO"] = change_log_df["Sent to ASO"].astype(bool).fillna(False)
if "Addressed?" in inquiry_log_df.columns:
    inquiry_log_df["Addressed?"] = inquiry_log_df["Addressed?"].astype(bool).fillna(False)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📄 Course Table", "📝 Change Log", "❓ Inquiry Log"])

# --- TAB 1: COURSE TABLE ---
with tab1:
    st.header("Course List")
    st.dataframe(courses_df, use_container_width=True)

    st.markdown("---")
    if is_admin:
        st.subheader("Admin: Edit Course")
        with st.form("edit_form"):
            selected = st.selectbox("Select Course to Edit", courses_df["Course"])
            course_row = courses_df[courses_df["Course"] == selected].iloc[0]

            new_title = st.text_input("New Title", course_row["Course"])
            new_attrs = st.text_input("New Attributes", course_row["Attribute(s)"])
            comment = st.text_area("Comment on Change")

            submitted = st.form_submit_button("Submit Edit")
            if submitted:
                idx = courses_df[courses_df["Course"] == selected].index[0]

                log_entry = {
                    "Course": selected,
                    "Old Title": courses_df.at[idx, "Course"],
                    "New Title": new_title,
                    "Old Attributes": courses_df.at[idx, "Attribute(s)"],
                    "New Attributes": new_attrs,
                    "Comment": comment,
                    "Submitted By": "Admin",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sent to ASO": False
                }

                courses_df.at[idx, "Course"] = new_title
                courses_df.at[idx, "Attribute(s)"] = new_attrs
                change_log_df = pd.concat([change_log_df, pd.DataFrame([log_entry])], ignore_index=True)

                change_log_ws.update([change_log_df.columns.values.tolist()] + change_log_df.astype(str).values.tolist())
                courses_ws.update([courses_df.columns.values.tolist()] + courses_df.values.tolist())
                st.success("Edit submitted and logged.")

    st.subheader("Advisor: Submit an Attribute Inquiry")
    with st.form("advisor_form"):
        advisor_name = st.text_input("Your Name")
        advisor_comment = st.text_area("Your question or comment")
        submitted_inquiry = st.form_submit_button("Submit Inquiry")
        if submitted_inquiry:
            log_entry = {
                "Name": advisor_name,
                "Comment": advisor_comment,
                "Addressed?": False,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            inquiry_log_df = pd.concat([inquiry_log_df, pd.DataFrame([log_entry])], ignore_index=True)
            inquiry_log_ws.update([inquiry_log_df.columns.tolist()] + inquiry_log_df.astype(str).values.tolist())
            st.success("Inquiry submitted.")

# --- TAB 2: CHANGE LOG ---
with tab2:
    st.header("Change Log")
    if not change_log_df.empty:
        editable_df = change_log_df.copy()
        editable_df["Comment"] = editable_df["Comment"].astype(str)
        editable_df["Sent to ASO"] = editable_df["Sent to ASO"].astype(bool)

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=([] if is_admin else list(editable_df.columns))
        )

        if is_admin and st.button("Save Change Log"):
            if not change_log_df.equals(edited_df):
                change_log_df = edited_df
                change_log_ws.update([change_log_df.columns.values.tolist()] + change_log_df.astype(str).values.tolist())
                st.success("Change log saved.")
    else:
        st.info("No change logs recorded yet.")

# --- TAB 3: INQUIRY LOG ---
with tab3:
    st.header("Inquiry Log")
    filter_unaddressed = st.checkbox("Show only unaddressed inquiries")
    filtered_df = inquiry_log_df[~inquiry_log_df["Addressed?"]] if filter_unaddressed else inquiry_log_df

    if not filtered_df.empty:
        editable_df = filtered_df.copy()
        editable_df["Comment"] = editable_df["Comment"].astype(str)
        editable_df["Addressed?"] = editable_df["Addressed?"].astype(bool)

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=([] if is_admin else list(editable_df.columns))
        )

        if is_admin and st.button("Save Inquiry Log"):
            if not inquiry_log_df.equals(edited_df):
                # Merge changes by Timestamp
                for idx, row in edited_df.iterrows():
                    original_idx = inquiry_log_df[inquiry_log_df["Timestamp"] == row["Timestamp"]].index
                    if not original_idx.empty:
                        inquiry_log_df.loc[original_idx[0], "Addressed?"] = row["Addressed?"]
                        inquiry_log_df.loc[original_idx[0], "Comment"] = row["Comment"]
                inquiry_log_ws.update([inquiry_log_df.columns.values.tolist()] + inquiry_log_df.astype(str).values.tolist())
                st.success("Inquiry log saved.")
    else:
        st.info("No inquiries submitted yet.")
