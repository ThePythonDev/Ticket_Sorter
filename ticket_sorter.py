import os
import platform
import re
import sys

import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# =========================================================
# BUNDLING HELPERS (For Standalone EXE/APP)
# =========================================================
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- Windows Path Setup ---
if platform.system() == "Windows":
    # Points to the folder we will bundle in the GitHub Action
    pytesseract.pytesseract.tesseract_cmd = get_resource_path(
        r"Tesseract-OCR\tesseract.exe"
    )
    os.environ["PATH"] += os.pathsep + get_resource_path("poppler-library/bin")

# --- Mac Path Setup ---
if platform.system() == "Darwin":
    # On Mac, we'll bundle the binary in the root of the app
    pytesseract.pytesseract.tesseract_cmd = get_resource_path("tesseract")


# =========================================================
# OCR LOGIC SECTION
# =========================================================
class TicketLogic:
    def process_file(self, file_path):
        images = []
        if file_path.lower().endswith(".pdf"):
            images = convert_from_path(file_path)
        else:
            images = [Image.open(file_path)]

        extracted_data = []
        for img in images:
            text_block = pytesseract.image_to_string(img)
            extracted_data.append(self.parse_fields(text_block))
        return extracted_data

    def parse_fields(self, text):
        patterns = {
            "Ticket_ID": r"(\d{9,10})",
            "Date_Time": r"Ticket Date/Time:\s*(.*)",
            "Applicant": r"Applicant:\s*(.*)",
            "Disaster": r"Disaster:\s*(.*)",
            "Program": r"Program:\s*(.*)",
            "Contractor": r"Contractor:\s*(.*)",
            "Sub-Contractor": r"Sub-Contractor:\s*(.*)",
            "Crew": r"Crew:\s*(.*)",
            "Supervisor": r"Supervisor:\s*(.*)",
            "Hazard_Type": r"Hazard Type:\s*(.*)",
            "GPS": r"GPS\(Lat,Lgn\):\s*(.*)",
            "Address": r"Address:\s*(.*)",
            "Measure": r"Measure:\s*([\d\.]+)",
            "Unit_Count": r"Unit Count:\s*(\d+)",
            "Monitor": r"Monitor:\s*(.*)",
        }

        row = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            row[field] = match.group(1).strip() if match else "N/A"
        return row


# =========================================================
# THREADING SECTION
# =========================================================
class ProcessingWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(list)

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths

    def run(self):
        logic = TicketLogic()
        all_results = []
        for i, path in enumerate(self.file_paths):
            filename = os.path.basename(path)
            self.status.emit(f"Processing ({i + 1}/{len(self.file_paths)}): {filename}")
            try:
                data_list = logic.process_file(path)
                all_results.extend(data_list)
            except Exception as e:
                self.status.emit(f"Error in {filename}: {str(e)}")

            prog_val = int(((i + 1) / len(self.file_paths)) * 100)
            self.progress.emit(prog_val)
        self.finished.emit(all_results)


# =========================================================
# GUI SECTION
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ticket OCR Standalone")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()
        self.label = QLabel("Select Tickets (JPG, PNG, PDF)")
        self.btn_upload = QPushButton("Select Files and Start")
        self.btn_upload.setFixedHeight(50)
        self.pbar = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout.addWidget(self.label)
        layout.addWidget(self.btn_upload)
        layout.addWidget(self.pbar)
        layout.addWidget(self.log_output)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.btn_upload.clicked.connect(self.handle_upload)

    def handle_upload(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Tickets", "", "Ticket Files (*.png *.jpg *.jpeg *.pdf)"
        )
        if files:
            self.btn_upload.setEnabled(False)
            self.log_output.clear()
            self.pbar.setValue(0)
            self.worker = ProcessingWorker(files)
            self.worker.status.connect(lambda s: self.log_output.append(s))
            self.worker.progress.connect(self.pbar.setValue)
            self.worker.finished.connect(self.handle_finished)
            self.worker.start()

    def handle_finished(self, results):
        self.btn_upload.setEnabled(True)
        if not results:
            self.log_output.append("\n❌ Extraction failed.")
            return

        df = pd.DataFrame(results)
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Spreadsheet", "Ticket_Data.xlsx", "Excel Files (*.xlsx)"
        )
        if save_path:
            df.to_excel(save_path, index=False)
            self.log_output.append(f"\n✅ SUCCESS! Saved to:\n{save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
