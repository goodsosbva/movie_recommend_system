"""Kiwi 형태소 분석과 BM25 기반 영화 추천."""

from __future__ import annotations

from typing import Any

from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi


CONTENT_TAGS = {"NNG", "NNP", "SL", "SH", "SN", "VV", "VA", "XR"}
WEIGHTS = {"bm25": 0.55, "genre": 0.25, "keyword": 0.15, "people": 0.05}
_kiwi = Kiwi(num_workers=0)


def tokenize(text: str) -> list[str]:
    """추천에 의미 있는 한국어 형태소만 남긴다."""
    if not text:
        return []
    return [token.form for token in _kiwi.tokenize(text) if token.tag in CONTENT_TAGS]


def build_bm25(movies: list[dict[str, Any]]) -> BM25Okapi:
    corpus = [movie["tokens"] for movie in movies]
    if not corpus or not any(corpus):
        raise ValueError("BM25 인덱스를 만들 수 있는 줄거리 토큰이 없습니다.")
    return BM25Okapi(corpus, k1=1.5, b=0.75)


def jaccard(left: list[Any], right: list[Any]) -> float:
    left_set, right_set = set(left), set(right)
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 0.0


def people_score(selected: dict[str, Any], candidate: dict[str, Any]) -> float:
    same_director = selected.get("director_id") == candidate.get("director_id") and bool(selected.get("director_id"))
    return 0.7 * float(same_director) + 0.3 * jaccard(selected["cast_ids"], candidate["cast_ids"])


def normalize(scores: list[float]) -> list[float]:
    maximum = max(scores, default=0.0)
    return [max(score, 0.0) / maximum if maximum > 0 else 0.0 for score in scores]


def reasons(scores: dict[str, float]) -> list[str]:
    result: list[str] = []
    if scores["genre"] >= 0.5:
        result.append("장르가 비슷합니다.")
    if scores["keyword"] >= 0.2:
        result.append("핵심 소재와 키워드가 겹칩니다.")
    if scores["bm25"] >= 0.45:
        result.append("줄거리의 주요 주제가 비슷합니다.")
    if scores["people"] >= 0.7:
        result.append("같은 감독이 참여했습니다.")
    return result or ["줄거리와 영화 정보의 관련도를 종합했습니다."]


def recommend(selected: dict[str, Any], movies: list[dict[str, Any]], bm25: BM25Okapi, limit: int = 10, candidate_limit: int = 100) -> list[dict[str, Any]]:
    """선택 영화를 검색 질의로 삼아 후보를 재정렬한다."""
    if limit < 1 or candidate_limit < limit:
        raise ValueError("추천 개수 설정이 올바르지 않습니다.")
    query = list(dict.fromkeys(selected.get("tokens") or tokenize(selected.get("overview", ""))))
    if not query:
        raise ValueError("선택한 영화에 추천 가능한 줄거리 정보가 없습니다.")
    raw_scores = list(bm25.get_scores(query))
    normalized = normalize(raw_scores)
    candidates = sorted(range(len(movies)), key=raw_scores.__getitem__, reverse=True)[:candidate_limit]
    ranked: list[dict[str, Any]] = []
    for index in candidates:
        movie = movies[index]
        if movie["id"] == selected["id"]:
            continue
        scores = {
            "bm25": normalized[index],
            "genre": jaccard(selected["genre_ids"], movie["genre_ids"]),
            "keyword": jaccard(selected["keyword_ids"], movie["keyword_ids"]),
            "people": people_score(selected, movie),
        }
        ranked.append({"movie": movie, "score": sum(scores[name] * WEIGHTS[name] for name in WEIGHTS), "reasons": reasons(scores)})
    ranked.sort(key=lambda item: (item["score"], item["movie"]["title"]), reverse=True)
    return ranked[:limit]
