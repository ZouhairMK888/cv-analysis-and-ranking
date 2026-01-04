from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def job_description_match(cv_text: str, job_description: str) -> float:
    if not job_description.strip():
        return 0.0

    docs = [cv_text, job_description]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    tfidf = vectorizer.fit_transform(docs)
    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]

    return round(similarity * 100, 2)
