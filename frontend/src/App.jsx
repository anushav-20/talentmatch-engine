import React, { useState } from "react";
import axios from "axios";

const API = "http://localhost:5000/api";

export default function App() {
  const [jdText, setJdText] = useState("");
  const [resumes, setResumes] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runMatch = async () => {
    if (!jdText.trim() || resumes.length === 0) {
      setError("Add a job description and at least one resume.");
      return;
    }
    setError("");
    setLoading(true);
    setResults(null);

    const formData = new FormData();
    formData.append("job_description_text", jdText);
    resumes.forEach((f) => formData.append("resumes", f));

    try {
      const res = await axios.post(`${API}/match`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(res.data.candidates);
    } catch (e) {
      setError(e.response?.data?.error || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎯 TalentMatch</h1>
        <p>Rank candidate resumes against a job description with NLP</p>
      </header>

      <div className="panel">
        <label>Job Description</label>
        <textarea rows={6} value={jdText} onChange={(e) => setJdText(e.target.value)} placeholder="Paste the job description..." />

        <label>Candidate Resumes (multiple)</label>
        <input type="file" multiple accept=".pdf,.docx,.txt" onChange={(e) => setResumes([...e.target.files])} />

        {error && <p className="error">{error}</p>}
        <button onClick={runMatch} disabled={loading}>{loading ? "Ranking..." : "Rank Candidates"}</button>
      </div>

      {results && (
        <div className="results">
          {results.map((c, i) => (
            <div key={c.name} className="candidate-card">
              <div className="candidate-header">
                <span className="rank">#{i + 1}</span>
                <strong>{c.name}</strong>
                <span className="score">{c.match_score}%</span>
              </div>
              <div className="chips">
                {c.matched_keywords.slice(0, 8).map((k) => <span key={k} className="chip match">{k}</span>)}
              </div>
              {c.missing_keywords.length > 0 && (
                <p className="missing">Missing: {c.missing_keywords.slice(0, 6).join(", ")}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
