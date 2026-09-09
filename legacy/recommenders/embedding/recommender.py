"""사전 계산한 문장 임베딩의 코사인 유사도 추천."""
from __future__ import annotations
from typing import Any
import numpy as np

def movie_text(movie: dict[str, Any], source: str = "metadata") -> str:
    """임베딩에 넣을 텍스트를 만든다.

    metadata는 현재 KOBIS에서 확보한 정보만 사용한다. plot은 모든 영화에
    줄거리가 있다고 확정된 별도 인덱스(줄거리만 있는 부분집합)를 만들 때 쓴다.
    combined은 전체 카탈로그처럼 줄거리가 있는 영화와 없는 영화가 섞여 있을 때
    쓴다 — 있으면 추가하고 없으면 조용히 생략한다.
    """
    if source not in ("metadata", "plot", "combined"):
        raise ValueError("source는 metadata, plot, combined 중 하나여야 합니다.")
    if source == "plot":
        overview = str(movie.get("overview", "")).strip()
        if not overview:
            raise ValueError("줄거리 임베딩에는 overview가 필요합니다.")
        return f"줄거리: {overview}\n장르: {' '.join(movie.get('genres', []))}"
    metadata = "\n".join(
        part for part in (
            f"장르: {' '.join(movie.get('genres', []))}" if movie.get("genres") else "",
            f"제작국: {movie.get('nation', '')}" if movie.get("nation") else "",
            f"감독: {' '.join(movie.get('directors', []))}" if movie.get("directors") else "",
            f"형식: {movie.get('type', '')}" if movie.get("type") else "",
        ) if part
    )
    if source == "metadata":
        return metadata
    overview = str(movie.get("overview", "")).strip()
    return f"{metadata}\n줄거리: {overview}" if overview else metadata

def recommend(selected: dict[str, Any], movies: list[dict[str, Any]], ids: list[str], embeddings: np.ndarray, limit: int = 10) -> list[dict[str, Any]]:
    if embeddings.ndim != 2 or len(movies) != len(ids) or len(ids) != len(embeddings):
        raise ValueError("영화 데이터와 임베딩 인덱스가 일치하지 않습니다. build_embeddings.py를 다시 실행하십시오.")
    try:
        selected_index = ids.index(str(selected["id"]))
    except ValueError as error:
        raise ValueError("선택한 영화의 임베딩이 없습니다.") from error
    scores = embeddings @ embeddings[selected_index]
    ranked = sorted((i for i in range(len(movies)) if i != selected_index), key=scores.__getitem__, reverse=True)
    return [{"movie": movies[i], "score": float(scores[i])} for i in ranked[:limit]]
