"""Kiwi 형태소 분석과 BM25 기반 영화 추천."""

from __future__ import annotations

from typing import Any

from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi


CONTENT_TAGS = {"NNG", "NNP", "SL", "SH", "SN", "VV", "VA", "XR"}
_kiwi = Kiwi(num_workers=0)


def tokenize(text: str) -> list[str]:
    return [token.form for token in _kiwi.tokenize(text) if token.tag in CONTENT_TAGS] if text else []


def build(documents: list[str]) -> BM25Okapi:
    tokens = [tokenize(document) for document in documents]
    if not any(tokens):
        raise ValueError("BM25 인덱스를 만들 수 있는 토큰이 없습니다.")
    return BM25Okapi(tokens, k1=1.5, b=0.75)


def rank(index: BM25Okapi, query: str) -> list[int]:
    scores = index.get_scores(tokenize(query))
    return sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
