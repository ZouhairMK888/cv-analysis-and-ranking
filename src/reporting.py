import io
import pandas as pd
from fpdf import FPDF


def generate_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Candidates")
    return output.getvalue()


def generate_pdf(df: pd.DataFrame) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Candidate Evaluation Report", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=10)

    for _, row in df.iterrows():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Name: {row['Name']}", ln=True)

        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, f"Email: {row['Email']}", ln=True)
        pdf.cell(0, 6, f"Phone: {row['Phone']}", ln=True)
        pdf.cell(0, 6, f"Experience: {row['Experience (Years)']} years", ln=True)
        pdf.cell(0, 6, f"Skills Count: {row['Skills Count']}", ln=True)
        pdf.multi_cell(0, 6, f"Skills: {', '.join(row['Skills'])}")
        pdf.cell(0, 6, f"Final Score: {row['Final Score']}", ln=True)

        if "Job Match (%)" in df.columns:
            pdf.cell(0, 6, f"Job Match: {row['Job Match (%)']}%", ln=True)

        pdf.ln(4)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin1")
