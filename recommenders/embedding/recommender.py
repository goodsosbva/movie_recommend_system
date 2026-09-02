"""사전 계산한 문장 임베딩의 코사인 유사도 추천."""
from __future__ import annotations
from typing import Any
import numpy as np

def movie_text(movie: dict[str, Any], source: str = "metadata") -> str:
    """임베딩에 넣을 텍스트를 만든다.

    metadata는 현재 KOBIS에서 확보한 정보만 사용한다. plot은 KMDb 줄거리가
    결합된 뒤 별도 인덱스를 만들 때 사용한다.
    """
    if source == "plot":
        overview = str(movie.get("overview", "")).strip()
        if not overview:
            raise ValueError("줄거리 임베딩에는 overview가 필요합니다.")
        return f"줄거리: {overview}\n장르: {' '.join(movie.get('genres', []))}"
    if source != "metadata":
        raise ValueError("source는 metadata 또는 plot이어야 합니다.")
    return "\n".join(
        part for part in (
            f"장르: {' '.join(movie.get('genres', []))}" if movie.get("genres") else "",
            f"제작국: {movie.get('nation', '')}" if movie.get("nation") else "",
            f"감독: {' '.join(movie.get('directors', []))}" if movie.get("directors") else "",
            f"형식: {movie.get('type', '')}" if movie.get("type") else "",
        ) if part
    )

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
