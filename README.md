# Course Attribute Tracker

This is a Streamlit web application for tracking, editing, and managing university course attributes.

## Features

- View a live table of all courses and their attributes
- Admin-only section to edit course titles and attributes
- Advisors can submit comments or inquiries per course
- Changes and inquiries are logged with timestamps
- Change log includes editable comments and a "Sent to ASO?" checkbox
- Simple password system to restrict editing permissions

## How to Use

1. Admin users enter a password in the sidebar to enable editing.
2. Non-admin users (e.g., advisors) can submit questions or comments tied to a course.
3. Admins can view and update a full change log.
4. All edits are tracked with timestamps and visible in the second tab.

## Setup (for local use)

1. Install Streamlit and pandas:
   ```
   pip install -r requirements.txt
   ```

2. Run the app:
   ```
   streamlit run app.py
   ```

3. Make sure `courses.csv` is in the same folder.

## Deployment

To deploy the app on [Streamlit Cloud](https://streamlit.io/cloud):

- Upload `app.py`, `courses.csv`, `requirements.txt`, and `README.md` to a public GitHub repository
- Link your GitHub to Streamlit Cloud and deploy directly

