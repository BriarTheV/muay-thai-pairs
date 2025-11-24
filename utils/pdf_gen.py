# utils/pdf_gen.py - PDF and Excel export generation

import pandas as pd
from fpdf import FPDF
from io import BytesIO
import streamlit as st


def generate_excel_fighters(fighters_df: pd.DataFrame, event_date: str = None) -> bytes:
    """Generate Excel file with fighter data in Russian format."""
    output = BytesIO()

    # Prepare fighter data with Russian columns
    export_df = pd.DataFrame()

    # Map to Russian column names
    russian_columns = {
        "дата": event_date or pd.Timestamp.now().strftime("%Y-%m-%d"),  # Event date
        "пол": fighters_df["Gender"],
        "фамилия и имя спортсмена": fighters_df["Name"],
        "дата рождения": fighters_df.get("DOB", pd.NaT),
        "полных лет": fighters_df["Age"],
        "возрастная категория": fighters_df.get("Age_Category", ""),
        "весовая категория": fighters_df["Weight_Class"],
        "класс": fighters_df.get("Class", ""),
        "город/клуб": fighters_df["Club"],
        "тренер": fighters_df["Trainer"],
        "количество боев": fighters_df["Record"],
        "количество побед": fighters_df.get("Wins", 0),
    }

    # Create DataFrame with Russian headers
    for rus_col, data in russian_columns.items():
        if isinstance(data, str):
            export_df[rus_col] = [data] * len(fighters_df)
        else:
            export_df[rus_col] = data

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Fighters sheet with Russian headers
        export_df.to_excel(writer, sheet_name="Спортсмены", index=False)

        # Summary sheet
        if not fighters_df.empty:
            summary = {
                "Всего спортсменов": [len(fighters_df)],
                "Пол": [fighters_df["Gender"].value_counts().to_dict()],
                "Весовые категории": [
                    fighters_df["Weight_Class"].value_counts().to_dict()
                ],
                "Средний возраст": [fighters_df["Age"].mean()],
                "Средний вес": [fighters_df["Weight"].mean()],
            }
            summary_df = pd.DataFrame(summary)
            summary_df.to_excel(writer, sheet_name="Сводка", index=False)

    output.seek(0)
    return output.getvalue()


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
