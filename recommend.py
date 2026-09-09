"""터미널에서 추천을 확인한다.

python recommend.py --title 친구
python recommend.py --title 기생충 --limit 5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from recommender import build_index, recommend

MOVIES_PATH = Path("data/movies.json")
TOKENS_PATH = Path("data/tokens.json")


def find(movies: list[dict], title: str) -> int:
    keyword = title.strip().casefold()
    matches = [i for i, movie in enumerate(movies) if keyword in movie["title"].casefold()]
    if not matches:
        raise SystemExit(f"오류: '{title}'과(와) 일치하는 영화가 없습니다.")
    if len(matches) > 1:
        first = movies[matches[0]]
        print(f"{len(matches)}편이 일치하여 첫 번째를 씁니다: {first['title']} ({first['year']})")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="BM25 유사 영화 추천")
    parser.add_argument("--title", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if not MOVIES_PATH.exists() or not TOKENS_PATH.exists():
        raise SystemExit("오류: data/movies.json 또는 data/tokens.json이 없습니다. python build_dataset.py를 먼저 실행하십시오.")

    movies = json.loads(MOVIES_PATH.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    selected = find(movies, args.title)
    index = build_index(tokens)

    base = movies[selected]
    print(f"\n기준: {base['title']} ({base['year']}) · {', '.join(base.get('genres', [])) or '장르 미상'}")
    print(f"줄거리: {base.get('overview') or '(없음)'}\n")
    for item in recommend(index, tokens, movies, selected, args.limit):
        movie = item["movie"]
        print(f"[{item['ratio']:.0%}] {movie['title']} ({movie['year']}) · {', '.join(movie.get('genres', [])) or '장르 미상'}")
        print(f"       공통 낱말: {', '.join(item['terms']) or '없음'}")
        if movie.get("overview"):
            print(f"       {movie['overview'][:80]}")


if __name__ == "__main__":
    main()
