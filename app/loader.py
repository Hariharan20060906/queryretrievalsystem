import os
import fitz  # PyMuPDF
from docx import Document as DocxReader

def load_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        doc = fitz.open(file_path)
        return [page.get_text() for page in doc]

    elif ext == ".docx":
        doc = DocxReader(file_path)
        return [para.text for para in doc.paragraphs if para.text.strip()]

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().split("\n\n")  # basic chunking

    elif ext in [".eml", ".email"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return [f.read()]  # treat entire email as one chunk

    else:
        raise ValueError(f"Unsupported file format: {ext}")
