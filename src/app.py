import pandas as pd
import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv
load_dotenv()


from matching import job_description_match
from ocr import extract_text_from_image, extract_text_from_pdf
from parser import (
    extract_email,
    extract_experience_years,
    extract_name,
    extract_phone,
    extract_skills,
)
from scoring import final_score
from reporting import generate_excel, generate_pdf
from email_service import send_email

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Automated Recruitment System", layout="wide")
st.title("📊 Automated Recruitment & Candidate Ranking System")

# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------
page = st.sidebar.radio(
    "📌 Menu",
    ["Candidate Analysis", "Invite Candidates"],
)

# ==================================================
# 🧠 CANDIDATE ANALYSIS (UNCHANGED)
# ==================================================
if page == "Candidate Analysis":

    st.subheader("📝 Job Description (Optional)")
    job_description = st.text_area("Paste the job description here", height=180)
    jd_provided = bool(job_description.strip())

    uploaded_files = st.file_uploader(
        "📤 Upload CVs (PDF, JPG, PNG)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    candidates = []

    if uploaded_files:
        with st.spinner("Analyzing CVs..."):
            for file in uploaded_files:
                if file.type == "application/pdf":
                    cv_text = extract_text_from_pdf(file)
                else:
                    image = Image.open(file)
                    cv_text = extract_text_from_image(image)

                skills = extract_skills(cv_text)
                experience = extract_experience_years(cv_text)

                job_match = (
                    job_description_match(cv_text, job_description)
                    if jd_provided
                    else 0
                )

                score = final_score(
                    experience,
                    len(skills),
                    job_match,
                    jd_provided,
                )

                candidates.append(
                    {
                        "Name": extract_name(cv_text),
                        "Email": extract_email(cv_text),
                        "Phone": extract_phone(cv_text),
                        "Experience (Years)": experience,
                        "Skills": skills,
                        "Skills Count": len(skills),
                        "Job Match (%)": job_match,
                        "Final Score": score,
                    }
                )

        df = (
            pd.DataFrame(candidates)
            .sort_values("Final Score", ascending=False)
            .reset_index(drop=True)
        )

        st.sidebar.header("🔎 Filters")

        exp_filter = st.sidebar.slider(
            "Minimum years of experience",
            int(df["Experience (Years)"].min()),
            int(df["Experience (Years)"].max()),
            int(df["Experience (Years)"].min()),
        )

        score_filter = st.sidebar.slider(
            "Minimum final score",
            float(df["Final Score"].min()),
            float(df["Final Score"].max()),
            float(df["Final Score"].min()),
        )

        filtered_df = df[
            (df["Experience (Years)"] >= exp_filter)
            & (df["Final Score"] >= score_filter)
        ].reset_index(drop=True)

        # ✅ SAVE DATA FOR OTHER PAGE
        st.session_state.filtered_df = filtered_df

        # -------------------------------
        # TABLE (KEPT)
        # -------------------------------
        st.subheader("📋 Candidate Ranking Table")
        st.dataframe(filtered_df, use_container_width=True)

        # -------------------------------
        # SELECTION FOR REPORTING (KEPT)
        # -------------------------------
        st.subheader("📋 Candidate Details")

        if "report_selected" not in st.session_state:
            st.session_state.report_selected = {}

        select_all = st.checkbox("✅ Select ALL candidates for report")

        if select_all:
            for i in filtered_df.index:
                st.session_state.report_selected[i] = True

        for i, row in filtered_df.iterrows():
            with st.expander(f"#{i+1} — {row['Name']} (Score: {row['Final Score']})"):
                checked = st.checkbox(
                    "Select for report",
                    value=st.session_state.report_selected.get(i, False),
                    key=f"report_cb_{i}",
                )
                st.session_state.report_selected[i] = checked

                st.write(f"📧 Email: {row['Email']}")
                st.write(f"📞 Phone: {row['Phone']}")
                st.write(f"⏳ Experience: {row['Experience (Years)']} years")
                st.write("🧠 Skills:")
                st.write(", ".join(row["Skills"]))

        # -------------------------------
        # REPORT EXPORT (KEPT)
        # -------------------------------
        st.subheader("📄 Generate Report")

        selected_indexes = [
            i for i, v in st.session_state.report_selected.items() if v
        ]

        report_df = (
            filtered_df.loc[selected_indexes]
            if selected_indexes
            else filtered_df
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📊 Download Excel",
                generate_excel(report_df),
                "candidates_report.xlsx",
            )
        with col2:
            st.download_button(
                "📄 Download PDF",
                generate_pdf(report_df),
                "candidates_report.pdf",
            )

    else:
        st.info("⬆️ Upload CVs to start analysis.")

# ==================================================
# 📨 INVITE CANDIDATES (NEW, SEPARATE)
# ==================================================
if page == "Invite Candidates":
    st.title("📨 Invite Candidates to Interview")

    if "filtered_df" not in st.session_state:
        st.warning("❌ Please analyze CVs first.")
        st.stop()

    df = st.session_state.filtered_df

    st.subheader("✅ Select Candidates to Invite")

    if "invite_selected" not in st.session_state:
        st.session_state.invite_selected = {}

    select_all = st.checkbox("✅ Select ALL candidates to invite")

    if select_all:
        for i in df.index:
            st.session_state.invite_selected[i] = True

    selected_indexes = []

    for i, row in df.iterrows():
        checked = st.checkbox(
            f"{row['Name']} — {row['Email']}",
            value=st.session_state.invite_selected.get(i, False),
            key=f"invite_cb_{i}",
        )
        st.session_state.invite_selected[i] = checked
        if checked:
            selected_indexes.append(i)

    st.subheader("📅 Interview Details")
    interview_date = st.date_input("Interview date")
    interview_time = st.time_input("Interview time")

    st.subheader("✉️ Email Content")
    email_subject = st.text_input("Email subject", "Interview Invitation")

    email_body = st.text_area(
        "Email message",
        value=(
            "Dear {name},\n\n"
            "We are pleased to inform you that your profile has been shortlisted.\n\n"
            "You are invited to attend an interview on:\n"
            "📅 Date: {date}\n"
            "⏰ Time: {time}\n\n"
            "Please confirm your availability.\n\n"
            "Best regards,\nHR Team"
        ),
        height=260,
    )

    if st.button("🚀 Send Invitations"):
        if not selected_indexes:
            st.error("❌ No candidates selected.")
            st.stop()

        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587

        # 🔐 Read credentials from environment variables
        SENDER_EMAIL = os.getenv("EMAIL_USER")
        SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

        if not SENDER_EMAIL or not SENDER_PASSWORD:
            st.error(
            "❌ Email credentials not found.\n\n"
            "Please set EMAIL_USER and EMAIL_PASSWORD as environment variables."
            )
            st.stop()

        sent, failed = 0, []

        for i in selected_indexes:
            row = df.loc[i]

            if not row["Email"]:
                failed.append(row["Name"])
                continue

            body = email_body.format(
                name=row["Name"],
                date=interview_date.strftime("%d %B %Y"),
                time=interview_time.strftime("%H:%M"),
            )

            try:
                send_email(
                    SMTP_SERVER,
                    SMTP_PORT,
                    SENDER_EMAIL,
                    SENDER_PASSWORD,
                    row["Email"],
                    email_subject,
                body,
                )
                sent += 1
            except Exception as e:
                failed.append(row["Name"])
        st.success(f"✅ Invitations sent to {sent} candidate(s)")

        if failed:
            st.warning("⚠️ Failed for: " + ", ".join(failed))
