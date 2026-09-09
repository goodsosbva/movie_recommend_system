"""Kiwi 형태소 분석과 BM25 유사도로 비슷한 영화를 찾는다.

문서 한 편 = 장르 + 제작국 + 감독 + (있으면) 한국어 줄거리.
추천은 "고른 영화의 문서를 그대로 검색어로 삼아 나머지를 순위 매기기"다.
"""
from __future__ import annotations

from typing import Any

from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

# 명사·외국어·수사·동사·형용사·어근만 남긴다. 조사와 어미는 검색에 방해가 된다.
CONTENT_TAGS = {"NNG", "NNP", "SL", "SH", "SN", "VV", "VA", "XR"}
_kiwi = Kiwi(num_workers=0)


def tokenize(text: str) -> list[str]:
    """한국어 문장에서 검색에 쓸 형태소만 뽑는다."""
    if not text:
        return []
    return [token.form for token in _kiwi.tokenize(text) if token.tag in CONTENT_TAGS]


def document(movie: dict[str, Any]) -> str:
    """영화 한 편을 BM25에 넣을 한 덩어리 텍스트로 만든다."""
    parts = [
        " ".join(movie.get("genres", [])),
        movie.get("nation", ""),
        " ".join(movie.get("directors", [])),
        str(movie.get("overview", "")).strip(),
    ]
    return "\n".join(part for part in parts if part)


def build_tokens(movies: list[dict[str, Any]]) -> list[list[str]]:
    """전체 카탈로그를 토큰 목록으로 바꾼다. 오래 걸리므로 한 번만 하고 저장한다."""
    return [tokenize(document(movie)) for movie in movies]


def build_index(tokens: list[list[str]]) -> BM25Okapi:
    if not any(tokens):
        raise ValueError("BM25 인덱스를 만들 토큰이 없습니다. build_dataset.py를 먼저 실행하십시오.")
    return BM25Okapi(tokens, k1=1.5, b=0.75)


def common_terms(query: list[str], document_tokens: list[str], limit: int = 6) -> list[str]:
    """왜 추천됐는지 보여줄 공통 낱말. 질의에 나온 순서를 지킨다."""
    shared = set(document_tokens)
    seen: list[str] = []
    for term in query:
        if term in shared and term not in seen:
            seen.append(term)
    return seen[:limit]


def recommend(index: BM25Okapi, tokens: list[list[str]], movies: list[dict[str, Any]], selected: int, limit: int = 10) -> list[dict[str, Any]]:
    """고른 영화와 비슷한 순으로 돌려준다. 자기 자신은 뺀다."""
    if not 0 <= selected < len(movies):
        raise ValueError("선택한 영화의 위치가 카탈로그 범위를 벗어났습니다.")
    if len(tokens) != len(movies):
        raise ValueError("영화 목록과 토큰 목록의 길이가 다릅니다. build_dataset.py를 다시 실행하십시오.")
    if limit < 1:
        raise ValueError("추천 편수는 1 이상이어야 합니다.")
    query = tokens[selected]
    if not query:
        raise ValueError("선택한 영화에는 검색에 쓸 정보가 없습니다.")
    scores = index.get_scores(query)
    ranked = sorted((i for i in range(len(movies)) if i != selected), key=scores.__getitem__, reverse=True)[:limit]
    best = float(scores[ranked[0]]) if ranked else 0.0
    return [
        {
            "movie": movies[i],
            "score": float(scores[i]),
            "ratio": float(scores[i]) / best if best > 0 else 0.0,
            "terms": common_terms(query, tokens[i]),
        }
        for i in ranked
    ]
