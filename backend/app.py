"""
TalentMatch - AI Resume Screening & Candidate-Job Matching Engine

Lets a recruiter upload a job description plus multiple candidate resumes,
then ranks candidates by TF-IDF + cosine similarity match score, with a
keyword-gap breakdown per candidate and detected tools/organizations via NER.
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from utils.parser import extract_text
from utils.matcher import rank_candidates

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024


def _read_uploaded_file(file_storage):
    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx", "txt"):
        raise ValueError(f"Unsupported file type for {filename}")
    path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(path)
    try:
        return extract_text(path, ext)
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/match", methods=["POST"])
def match():
    if "job_description" not in request.files and "job_description_text" not in request.form:
        return jsonify({"error": "Provide a job_description file or job_description_text"}), 400

    resume_files = request.files.getlist("resumes")
    if not resume_files:
        return jsonify({"error": "At least one resume file is required"}), 400

    try:
        if "job_description" in request.files:
            jd_text = _read_uploaded_file(request.files["job_description"])
        else:
            jd_text = request.form["job_description_text"]

        candidates = []
        for f in resume_files:
            text = _read_uploaded_file(f)
            candidates.append({"name": f.filename, "text": text})

        ranked = rank_candidates(jd_text, candidates)
        return jsonify({"candidates": ranked, "total_candidates": len(ranked)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
