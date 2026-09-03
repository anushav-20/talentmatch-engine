"""Extract raw text from resume/job description files (PDF, DOCX, TXT)."""
import docx
import pdfplumber


def extract_text(filepath: str, ext: str) -> str:
    if ext == "pdf":
        text = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text.append(t)
        return "\n".join(text)
    if ext == "docx":
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"Unsupported file type: {ext}")
