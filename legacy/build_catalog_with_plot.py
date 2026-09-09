"""KOBIS 전체 카탈로그에 확보된 줄거리를 덧붙여 하나의 파일로 합친다.

OMDb 캐시(data/omdb_overview_cache.json)를 우선 사용하고, 나중에 같은 형식의
KMDb 캐시(data/kmdb_overview_cache.json, {영화id: 줄거리})가 생기면 그쪽을
우선시켜 자동으로 덮어쓴다. 줄거리가 없는 영화는 overview를 빈 문자열로 둔다.
"""
from __future__ import annotations

import json
from pathlib import Path

CATALOG_PATH = Path("data/kobis_catalog.json")
OUTPUT_PATH = Path("data/kobis_catalog_enriched.json")
# 뒤에 있는 소스가 앞선 소스의 줄거리를 덮어쓴다. KMDb가 한국 영화 특화라 우선순위가 더 높다.
OVERVIEW_SOURCES = [Path("data/omdb_overview_cache.json"), Path("data/kmdb_overview_cache.json")]


def load_overviews() -> dict[str, str]:
    overviews: dict[str, str] = {}
    for path in OVERVIEW_SOURCES:
        if not path.exists():
            continue
        cache = json.loads(path.read_text(encoding="utf-8"))
        overviews.update({movie_id: overview for movie_id, overview in cache.items() if overview})
    return overviews


def build() -> tuple[int, int]:
    movies = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    overviews = load_overviews()
    enriched = [{**movie, "overview": overviews.get(movie["id"], "")} for movie in movies]
    OUTPUT_PATH.write_text(json.dumps(enriched, ensure_ascii=False), encoding="utf-8")
    return len(enriched), sum(1 for movie in enriched if movie["overview"])


if __name__ == "__main__":
    total, with_overview = build()
    print(f"완료: 전체 {total:,}편 중 {with_overview:,}편에 줄거리를 채워 {OUTPUT_PATH}에 저장했습니다.")
