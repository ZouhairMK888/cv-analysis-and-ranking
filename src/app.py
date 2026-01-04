import pandas as pd
import streamlit as st
from PIL import Image

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

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Automated Recruitment System", layout="wide")
st.title("📊 Automated Recruitment & Candidate Ranking System")

st.markdown(
    """
    Upload CVs in **PDF or image format**.
    Optionally add a **job description**.
    Use filters to shortlist candidates.
    """
)

# --------------------------------------------------
# JOB DESCRIPTION
# --------------------------------------------------
st.subheader("📝 Job Description (Optional)")
job_description = st.text_area("Paste the job description here", height=180)
jd_provided = bool(job_description.strip())

# --------------------------------------------------
# UPLOAD CVS (PDF + IMAGES)
# --------------------------------------------------
uploaded_files = st.file_uploader(
    "📤 Upload CVs (PDF, JPG, PNG)",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

candidates = []

# --------------------------------------------------
# PROCESS CVS
# --------------------------------------------------
if uploaded_files:
    with st.spinner("Analyzing CVs..."):
        for file in uploaded_files:
            if file.type == "application/pdf":
                cv_text = extract_text_from_pdf(file)
            else:
                image = Image.open(file)
                cv_text = extract_text_from_image(image)

            name = extract_name(cv_text)
            email = extract_email(cv_text)
            phone = extract_phone(cv_text)
            skills = extract_skills(cv_text)
            experience = extract_experience_years(cv_text)

            job_match = (
                job_description_match(cv_text, job_description) if jd_provided else 0
            )

            score = final_score(
                experience_years=experience,
                skills_count=len(skills),
                job_match_score=job_match,
                jd_provided=jd_provided,
            )

            candidates.append(
                {
                    "Name": name,
                    "Email": email,
                    "Phone": phone,
                    "Experience (Years)": experience,
                    "Skills Count": len(skills),
                    "Skills": skills,
                    "Job Match (%)": job_match,
                    "Final Score": score,
                }
            )

    # --------------------------------------------------
    # DATAFRAME
    # --------------------------------------------------
    df = (
        pd.DataFrame(candidates)
        .sort_values(by="Final Score", ascending=False)
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # FILTERS
    # --------------------------------------------------
    st.sidebar.header("🔎 Filters")

    # Experience
    min_exp, max_exp = (
        int(df["Experience (Years)"].min()),
        int(df["Experience (Years)"].max()),
    )
    exp_filter = st.sidebar.slider(
        "Minimum years of experience", min_exp, max_exp, min_exp
    )

    # Score filter
    min_score, max_score = (
        float(df["Final Score"].min()),
        float(df["Final Score"].max()),
    )
    score_filter = st.sidebar.slider(
        "Minimum final score", min_score, max_score, min_score
    )

    # Skills
    all_skills = sorted({s for lst in df["Skills"] for s in lst})
    selected_skills = st.sidebar.multiselect("Required skills", all_skills)

    # Apply filters
    filtered_df = df[
        (df["Experience (Years)"] >= exp_filter) & (df["Final Score"] >= score_filter)
    ]

    if selected_skills:
        filtered_df = filtered_df[
            filtered_df["Skills"].apply(
                lambda s: all(skill in s for skill in selected_skills)
            )
        ]

    filtered_df = filtered_df.reset_index(drop=True)

    # --------------------------------------------------
    # RESULTS
    # --------------------------------------------------
    if filtered_df.empty:
        st.warning("No candidates match the selected filters.")
    else:
        best = filtered_df.iloc[0]

        st.success(
            f"🏆 Best Candidate: **{best['Name']}** "
            f"(Score: {best['Final Score']}"
            f"{' | Job Match: ' + str(best['Job Match (%)']) + '%' if jd_provided else ''})"
        )

        st.subheader("📋 Candidate Ranking Table")

        columns = [
            "Name",
            "Email",
            "Phone",
            "Experience (Years)",
            "Skills Count",
            "Final Score",
        ]
        if jd_provided:
            columns.insert(-1, "Job Match (%)")

        st.dataframe(filtered_df[columns], use_container_width=True)

        st.subheader("🔍 Candidate Details")
        for i, row in filtered_df.iterrows():
            with st.expander(f"#{i + 1} — {row['Name']} (Score: {row['Final Score']})"):
                st.write(f"📧 Email: {row['Email']}")
                st.write(f"📞 Phone: {row['Phone']}")
                st.write(f"⏳ Experience: {row['Experience (Years)']} years")
                st.write("🧠 Skills:")
                st.write(", ".join(row["Skills"]))

else:
    st.info("⬆️ Upload CVs to start analysis.")
