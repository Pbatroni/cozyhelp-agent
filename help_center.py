"""Cozy Cart help center: keyword search over sample articles (v1).

Later this can be swapped for the Front Knowledge Base API without
changing the agent, as long as the return shapes stay the same.
"""

import json
import re
from pathlib import Path

ARTICLES_FILE = Path(__file__).resolve().parent / "data" / "articles.json"

# An article needs at least this score to count as a match.
# Tuned with test_search.py (title word = 3, keyword = 2, body word = 1).
MIN_SCORE = 7

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "do", "does", "for",
    "from", "get", "how", "i", "if", "in", "is", "it", "me", "my", "of",
    "on", "or", "the", "this", "to", "was", "what", "when", "where", "why",
    "will", "with", "you", "your", "it's", "i'm", "im", "please", "hi",
    "hello", "want", "need", "about", "just", "there", "have", "has",
}


def _normalize(word: str) -> str:
    """Lowercase and strip simple endings so 'returning' matches 'return'."""
    word = word.lower()
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)]
            # "shipping" -> "shipp" -> "ship"
            if len(word) >= 4 and word[-1] == word[-2]:
                word = word[:-1]
            break
    return word


def _words(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z']+", text)
    return {_normalize(t) for t in tokens if t.lower() not in STOPWORDS}


def _load_articles() -> list[dict]:
    return json.loads(ARTICLES_FILE.read_text())


def _score(query_words: set[str], query_text: str, article: dict) -> int:
    score = 3 * len(query_words & _words(article["title"]))
    for keyword in article["keywords"]:
        # Multi-word keywords ("send back") match when all their words appear
        if " " in keyword:
            if _words(keyword) and _words(keyword) <= query_words:
                score += 2
        elif _normalize(keyword) in query_words:
            score += 2
    score += len(query_words & _words(article["body"]))
    return score


def search_help_center(query: str, max_results: int = 3) -> list[dict]:
    """Return the best-matching articles: id, title, short excerpt, url.

    Returns an empty list when nothing scores at least MIN_SCORE.
    """
    query_words = _words(query)
    query_text = query.lower()
    scored = []
    for article in _load_articles():
        score = _score(query_words, query_text, article)
        if score >= MIN_SCORE:
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "id": article["id"],
            "title": article["title"],
            "excerpt": article["body"][:160],
            "url": article["url"],
        }
        for _, article in scored[:max_results]
    ]


def get_article(article_id: str) -> dict | None:
    """Return one full article (title, content, url), or None if not found."""
    for article in _load_articles():
        if article["id"] == article_id:
            return {
                "id": article["id"],
                "title": article["title"],
                "content": article["body"],
                "url": article["url"],
            }
    return None
