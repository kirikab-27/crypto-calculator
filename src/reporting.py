"""Reporting utilities for CSV and PDF summaries."""

from typing import Any, Dict
import csv


def generate_csv_report(summary: Dict[str, Any], filepath: str) -> None:
    """Write summary dictionary to a CSV file.

    Parameters
    ----------
    summary : Dict[str, Any]
        Dictionary containing calculation results.
    filepath : str
        Destination CSV path.
    """
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        for key, value in summary.items():
            writer.writerow([key, value])


def generate_pdf_report(summary: Dict[str, Any], filepath: str) -> None:
    """Write summary dictionary to a PDF file.

    If the optional ``fpdf`` package is available it will be used to generate a
    simple PDF. Otherwise the report is written as plain text with a ``.pdf``
    extension.
    """
    try:
        from fpdf import FPDF  # type: ignore
    except Exception:
        with open(filepath, "w") as f:
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")
        return

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Calculation Summary", ln=True, align="C")
    pdf.ln(5)
    for key, value in summary.items():
        pdf.cell(0, 10, f"{key}: {value}", ln=True)
    pdf.output(filepath)
