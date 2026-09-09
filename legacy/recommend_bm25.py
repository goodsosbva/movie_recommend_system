"""줄거리(있으면)+메타데이터를 합친 텍스트로 BM25 유사 영화를 찾는다.

python recommend_bm25.py --title 인터스텔라
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recommenders.bm25.recommender import build, rank
from recommenders.embedding.recommender import movie_text

CATALOG_PATH = Path("data/kobis_catalog_enriched.json")


def find_movie(movies: list[dict], title: str) -> int:
    matches = [i for i, movie in enumerate(movies) if title.strip().casefold() in movie["title"].casefold()]
    if not matches:
        raise SystemExit(f"오류: '{title}'과(와) 일치하는 영화가 없습니다.")
    if len(matches) > 1:
        print(f"'{title}'과(와) 일치하는 {len(matches)}편 중 첫 번째를 기준으로 사용합니다: {movies[matches[0]]['title']} ({movies[matches[0]]['year']})")
    return matches[0]


def recommend(movies: list[dict], selected_index: int, limit: int = 10) -> list[dict]:
    documents = [movie_text(movie, source="combined") for movie in movies]
    index = build(documents)
    ranked = [i for i in rank(index, documents[selected_index]) if i != selected_index]
    return [movies[i] for i in ranked[:limit]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="줄거리 포함 BM25로 유사 영화 추천")
    parser.add_argument("--title", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if not CATALOG_PATH.exists():
        raise SystemExit(f"오류: {CATALOG_PATH}가 없습니다. python build_catalog_with_plot.py를 먼저 실행하십시오.")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    selected = find_movie(catalog, args.title)
    print(f"기준 영화: {catalog[selected]['title']} ({catalog[selected]['year']}) · 줄거리 있음: {bool(catalog[selected].get('overview'))}")
    for movie in recommend(catalog, selected, args.limit):
        print(f"- {movie['title']} ({movie['year']}) · {', '.join(movie.get('genres', [])) or '장르 미상'} · 줄거리 있음: {bool(movie.get('overview'))}")
