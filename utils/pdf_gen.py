# utils/pdf_gen.py - PDF and Excel export generation

import pandas as pd
from fpdf import FPDF
from io import BytesIO
import streamlit as st


def generate_excel_matches(matches_df: pd.DataFrame) -> bytes:
    """Generate Excel file with match data."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Matches sheet
        matches_df.to_excel(writer, sheet_name="Matches", index=False)

        # Summary sheet
        if not matches_df.empty:
            summary = {
                "Total Matches": [len(matches_df)],
                "Average Weight Diff": [matches_df["Weight_Diff"].mean()],
                "Max Weight Diff": [matches_df["Weight_Diff"].max()],
                "Average Age Diff": [matches_df["Age_Diff"].mean()],
                "Max Age Diff": [matches_df["Age_Diff"].max()],
                "Genders": [matches_df["Gender"].value_counts().to_dict()],
                "Weight Classes": [matches_df["Weight_Class"].value_counts().to_dict()],
            }
            summary_df = pd.DataFrame(summary)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)

    output.seek(0)
    return output.getvalue()


def generate_pdf_bout_sheets(
    matches_df: pd.DataFrame, event_name: str = "Muay Thai Competition"
) -> bytes:
    """Generate PDF with bout sheets."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for _, match in matches_df.iterrows():
        pdf.add_page()

        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, event_name, ln=True, align="C")
        pdf.cell(0, 10, f"Match #{match['Match_ID']}", ln=True, align="C")
        pdf.ln(10)

        # Bout details
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Weight Class: {match['Weight_Class']}", ln=True)
        pdf.cell(0, 8, f"Gender: {match['Gender']}", ln=True)
        pdf.ln(5)

        # Red Corner
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(255, 0, 0)  # Red
        pdf.cell(0, 10, "RED CORNER", ln=True, align="L")
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Name: {match['Red_Corner']}", ln=True)
        pdf.cell(0, 8, f"Club: {match['Red_Club']}", ln=True)
        pdf.cell(0, 8, f"Weight: {match['Red_Weight']} kg", ln=True)
        pdf.cell(0, 8, f"Age: {match['Red_Age']}", ln=True)
        pdf.cell(0, 8, f"Record: {match['Red_Record']}", ln=True)
        pdf.ln(5)

        # Blue Corner
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 255)  # Blue
        pdf.cell(0, 10, "BLUE CORNER", ln=True, align="L")
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Name: {match['Blue_Corner']}", ln=True)
        pdf.cell(0, 8, f"Club: {match['Blue_Club']}", ln=True)
        pdf.cell(0, 8, f"Weight: {match['Blue_Weight']} kg", ln=True)
        pdf.cell(0, 8, f"Age: {match['Blue_Age']}", ln=True)
        pdf.cell(0, 8, f"Record: {match['Blue_Record']}", ln=True)
        pdf.ln(10)

        # Signatures
        pdf.cell(80, 10, "Red Corner Signature: ____________________", ln=False)
        pdf.cell(80, 10, "Blue Corner Signature: ____________________", ln=True)
        pdf.ln(5)
        pdf.cell(80, 10, "Referee Signature: ____________________", ln=False)
        pdf.cell(80, 10, "Judge Signature: ____________________", ln=True)

    # Output to bytes
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output.getvalue()
