import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Course Attribute Tracker", layout="wide")

# --- USER PERMISSION SETUP ---
AUTHORIZED_USERS = {"Esia1957"}
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

# --- DATA LOADING ---
def load_courses():
    df = pd.DataFrame(courses_ws.get_all_records())
    df.columns = df.columns.str.strip()
    return df

def load_log(ws):
    df = pd.DataFrame(ws.get_all_records())
    df.columns = [str(col).strip() for col in df.columns]
    return df

if "courses_df" not in st.session_state:
    st.session_state.courses_df = load_courses()

if "change_log_df" not in st.session_state:
    st.session_state.change_log_df = load_log(change_log_ws) if change_log_ws.get_all_values() else pd.DataFrame(columns=[
        "Course", "Old Title", "New Title", "Old Attributes", "New Attributes",
        "Comment", "Submitted By", "Timestamp", "Sent to ASO"
    ])

if "inquiry_log_df" not in st.session_state:
    st.session_state.inquiry_log_df = load_log(inquiry_log_ws) if inquiry_log_ws.get_all_values() else pd.DataFrame(columns=[
        "Name", "Comment", "Addressed?", "Timestamp"
    ])

# --- SETUP LOCAL CHECKBOX STATE ---
if "sent_to_aso" not in st.session_state:
    st.session_state.sent_to_aso = {i: row.get("Sent to ASO", False) for i, row in st.session_state.change_log_df.iterrows()}

if "addressed" not in st.session_state:
    st.session_state.addressed = {i: row.get("Addressed?", False) for i, row in st.session_state.inquiry_log_df.iterrows()}

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📄 Course Table", "📝 Change Log", "❓ Inquiry Log"])

# --- TAB 1: COURSE TABLE ---
with tab1:
    st.header("Course List")
    st.dataframe(st.session_state.courses_df, use_container_width=True)

    st.markdown("---")
    if is_admin:
        st.subheader("Admin: Edit Course")
        with st.form("edit_form"):
            selected = st.selectbox("Select Course to Edit", st.session_state.courses_df["Course"])
            course_row = st.session_state.courses_df[st.session_state.courses_df["Course"] == selected].iloc[0]

            new_title = st.text_input("New Title", course_row["Course"])
            new_attrs = st.text_input("New Attributes", course_row["Attribute(s)"])
            comment = st.text_area("Comment on Change")

            submitted = st.form_submit_button("Submit Edit")
            if submitted:
                idx = st.session_state.courses_df[st.session_state.courses_df["Course"] == selected].index[0]
                log_entry = {
                    "Course": selected,
                    "Old Title": st.session_state.courses_df.at[idx, "Course"],
                    "New Title": new_title,
                    "Old Attributes": st.session_state.courses_df.at[idx, "Attribute(s)"],
                    "New Attributes": new_attrs,
                    "Comment": comment,
                    "Submitted By": "Admin",
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Sent to ASO": False
                }
                st.session_state.courses_df.at[idx, "Course"] = new_title
                st.session_state.courses_df.at[idx, "Attribute(s)"] = new_attrs
                st.session_state.change_log_df = pd.concat([st.session_state.change_log_df, pd.DataFrame([log_entry])], ignore_index=True)
                st.session_state.sent_to_aso[len(st.session_state.change_log_df) - 1] = False
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
            st.session_state.inquiry_log_df = pd.concat([st.session_state.inquiry_log_df, pd.DataFrame([log_entry])], ignore_index=True)
            st.session_state.addressed[len(st.session_state.inquiry_log_df) - 1] = False
            st.success("Inquiry submitted.")

# --- TAB 2: CHANGE LOG ---
with tab2:
    st.header("Change Log")
    df = st.session_state.change_log_df.copy()
    for i in df.index:
        st.session_state.sent_to_aso[i] = st.checkbox("Sent to ASO", value=st.session_state.sent_to_aso.get(i, False), key=f"aso_{i}")
    if is_admin and st.button("Save Change Log"):
        for i in df.index:
            df.at[i, "Sent to ASO"] = st.session_state.sent_to_aso[i]
        st.session_state.change_log_df = df
        change_log_ws.update([df.columns.tolist()] + df.astype(str).values.tolist())
        courses_ws.update([st.session_state.courses_df.columns.tolist()] + st.session_state.courses_df.values.tolist())
        st.success("Change log saved.")

# --- TAB 3: INQUIRY LOG ---
with tab3:
    st.header("Inquiry Log")
    filter_unaddressed = st.checkbox("Show only unaddressed inquiries")
    df = st.session_state.inquiry_log_df.copy()
    if filter_unaddressed:
        df = df[df.index.map(lambda i: not st.session_state.addressed.get(i, False))]
    for i in df.index:
        st.session_state.addressed[i] = st.checkbox("Addressed?", value=st.session_state.addressed.get(i, False), key=f"inq_{i}")
    if is_admin and st.button("Save Inquiry Log"):
        for i in df.index:
            st.session_state.inquiry_log_df.at[i, "Addressed?"] = st.session_state.addressed[i]
        inquiry_log_ws.update([st.session_state.inquiry_log_df.columns.tolist()] + st.session_state.inquiry_log_df.astype(str).values.tolist())
        st.success("Inquiry log saved.")

