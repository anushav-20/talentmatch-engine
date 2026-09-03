"""
Core matching engine: combines TF-IDF cosine similarity with spaCy named
entity recognition to rank multiple candidate resumes against a single job
description, and surfaces a keyword gap analysis per candidate.
"""
import re
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nlp = spacy.load("en_core_web_sm")

SKILL_ENTITY_LABELS = {"ORG", "PRODUCT", "LANGUAGE"}


def extract_entities(text: str):
    """Pulls out organizations, tools/products, and languages mentioned —
    a lightweight proxy for 'skills and qualifications' extraction."""
    doc = nlp(text[:100000])
    entities = {label: set() for label in SKILL_ENTITY_LABELS}
    for ent in doc.ents:
        if ent.label_ in SKILL_ENTITY_LABELS:
            entities[ent.label_].add(ent.text.strip())
    return {k: sorted(v) for k, v in entities.items()}


def _tfidf_similarity(jd_text: str, resume_texts: list[str]) -> list[float]:
    corpus = [jd_text] + resume_texts
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1, 2))
    tfidf = vectorizer.fit_transform(corpus)
    jd_vector = tfidf[0:1]
    resume_vectors = tfidf[1:]
    scores = cosine_similarity(jd_vector, resume_vectors)[0]
    return scores.tolist(), vectorizer


def _keyword_gap(jd_text: str, resume_text: str, vectorizer) -> dict:
    jd_terms = set(vectorizer.build_analyzer()(jd_text))
    resume_terms = set(vectorizer.build_analyzer()(resume_text))
    # Only surface terms the vectorizer actually considered informative
    vocab = set(vectorizer.vocabulary_.keys())
    jd_terms &= vocab
    resume_terms &= vocab

    missing = sorted(jd_terms - resume_terms)[:15]
    matched = sorted(jd_terms & resume_terms)[:15]
    return {"matched_keywords": matched, "missing_keywords": missing}


def rank_candidates(jd_text: str, candidates: list[dict]) -> list[dict]:
    """candidates: list of {"name": str, "text": str}"""
    resume_texts = [c["text"] for c in candidates]
    scores, vectorizer = _tfidf_similarity(jd_text, resume_texts)

    results = []
    for candidate, score in zip(candidates, scores):
        gap = _keyword_gap(jd_text, candidate["text"], vectorizer)
        entities = extract_entities(candidate["text"])
        results.append({
            "name": candidate["name"],
            "match_score": round(float(score) * 100, 1),
            **gap,
            "detected_tools_orgs": entities["ORG"][:10] + entities["PRODUCT"][:10],
        })

    return sorted(results, key=lambda r: r["match_score"], reverse=True)
