import csv
import types
import sys
from crypto_calculator.reporting import generate_csv_report, generate_pdf_report


def test_generate_csv_report(tmp_path):
    summary = {"a": 1, "b": 2}
    file_path = tmp_path / "report.csv"
    generate_csv_report(summary, str(file_path))

    with open(file_path, newline="") as f:
        rows = list(csv.reader(f))

    assert rows == [["key", "value"], ["a", "1"], ["b", "2"]]


def test_generate_pdf_report_without_fpdf(tmp_path, monkeypatch):
    summary = {"x": 10}
    file_path = tmp_path / "report.pdf"

    # Simulate missing fpdf by providing empty module
    monkeypatch.setitem(sys.modules, "fpdf", types.ModuleType("fpdf"))

    generate_pdf_report(summary, str(file_path))

    with open(file_path) as f:
        content = f.read().splitlines()

    assert content == ["x: 10"]


class DummyFPDF:
    def __init__(self):
        self.lines = []

    def add_page(self):
        pass

    def set_font(self, *args, **kwargs):
        pass

    def cell(self, w, h, txt, ln=False, align=None):
        self.lines.append(txt)

    def ln(self, h):
        pass

    def output(self, filepath):
        with open(filepath, "w") as f:
            for line in self.lines:
                f.write(f"{line}\n")


def test_generate_pdf_report_with_fpdf(tmp_path, monkeypatch):
    summary = {"x": 10, "y": 20}
    file_path = tmp_path / "report.pdf"

    dummy_module = types.ModuleType("fpdf")
    dummy_module.FPDF = DummyFPDF
    monkeypatch.setitem(sys.modules, "fpdf", dummy_module)

    generate_pdf_report(summary, str(file_path))

    with open(file_path) as f:
        lines = f.read().splitlines()

    expected = [
        "Calculation Summary",
        "x: 10",
        "y: 20",
    ]
    assert lines == expected
