"""KOBIS 카탈로그에 한국어 줄거리를 합치고, BM25용 토큰까지 미리 만들어 저장한다.

입력
  data/kobis_catalog.json   KOBIS에서 수집한 전체 영화 목록
  data/overview_ko.json     {영화코드: 한국어 줄거리}. 여러 개면 뒤가 앞을 덮는다.
출력
  data/movies.json          줄거리를 채워 넣은 카탈로그
  data/tokens.json          영화별 형태소 토큰 (앱 시작을 빠르게 하기 위한 캐시)
"""
from __future__ import annotations

import json
from pathlib import Path

from recommender import build_tokens

CATALOG_PATH = Path("data/kobis_catalog.json")
# 뒤에 있는 파일이 앞선 파일의 줄거리를 덮어쓴다. KMDb가 생기면 목록 끝에 추가만 하면 된다.
OVERVIEW_PATHS = [Path("data/overview_ko.json"), Path("data/overview_ko_kmdb.json")]
MOVIES_PATH = Path("data/movies.json")
TOKENS_PATH = Path("data/tokens.json")


def load_overviews() -> dict[str, str]:
    overviews: dict[str, str] = {}
    for path in OVERVIEW_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"오류: {path}의 최상위 값은 {{영화코드: 줄거리}} 객체여야 합니다.")
        overviews.update({key: value.strip() for key, value in data.items() if isinstance(value, str) and value.strip()})
        print(f"{path}: 줄거리 {len(data):,}건 읽음")
    return overviews


def main() -> None:
    if not CATALOG_PATH.exists():
        raise SystemExit(f"오류: {CATALOG_PATH}가 없습니다. python build_kobis_catalog.py를 먼저 실행하십시오.")
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    overviews = load_overviews()
    movies = [{**movie, "overview": overviews.get(str(movie["id"]), "")} for movie in catalog]
    filled = sum(1 for movie in movies if movie["overview"])

    MOVIES_PATH.parent.mkdir(exist_ok=True)
    MOVIES_PATH.write_text(json.dumps(movies, ensure_ascii=False), encoding="utf-8")
    print(f"{MOVIES_PATH}: 전체 {len(movies):,}편 중 {filled:,}편에 줄거리를 채웠습니다.")

    print("형태소 분석 중입니다. 몇 분 걸립니다...")
    tokens = build_tokens(movies)
    TOKENS_PATH.write_text(json.dumps(tokens, ensure_ascii=False), encoding="utf-8")
    empty = sum(1 for row in tokens if not row)
    print(f"{TOKENS_PATH}: 토큰 저장 완료. 토큰이 하나도 없는 영화 {empty:,}편.")


if __name__ == "__main__":
    main()
