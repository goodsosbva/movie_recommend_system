"""OMDb API로 KOBIS 카탈로그에 영문 줄거리를 보강한다."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

CATALOG_PATH = Path("data/kobis_catalog.json")
CACHE_PATH = Path("data/omdb_overview_cache.json")
OUTPUT_PATH = Path("data/kobis_catalog_plot.json")
BASE_URL = "http://www.omdbapi.com/"


def fetch_overview(session: requests.Session, api_key: str, title: str, year: str) -> str:
    """매칭에 실패하거나 줄거리가 없으면 빈 문자열을 돌려준다."""
    response = session.get(BASE_URL, params={"apikey": api_key, "t": title, "y": year}, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("Response") != "True":
        return ""
    plot = data.get("Plot", "")
    return plot if plot and plot != "N/A" else ""


def collect(limit: int, pause: float) -> tuple[int, int]:
    load_dotenv()
    api_key = os.getenv("OMDB_API_KEY", "")
    if not api_key:
        raise SystemExit("오류: OMDB_API_KEY 환경변수를 설정하십시오.")

    movies = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    cache: dict[str, str] = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    session = requests.Session()

    calls = 0
    for movie in movies:
        if calls >= limit:
            break
        movie_id = movie["id"]
        if movie_id in cache:
            continue
        title = movie.get("original_title") or movie["title"]
        cache[movie_id] = fetch_overview(session, api_key, title, movie.get("year", ""))
        calls += 1
        if calls % 50 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"{calls}건 조회, 누적 캐시 {len(cache)}건")
        time.sleep(pause)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    matched = [{**movie, "overview": cache[movie["id"]]} for movie in movies if cache.get(movie["id"])]
    OUTPUT_PATH.write_text(json.dumps(matched, ensure_ascii=False), encoding="utf-8")
    return calls, len(matched)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OMDb 줄거리로 KOBIS 카탈로그 보강 (하루 여러 번 나눠 실행 가능)")
    parser.add_argument("--limit", type=int, default=900, help="이번 실행에서 새로 조회할 최대 건수 (무료 키 하루 1,000건 제한)")
    parser.add_argument("--pause", type=float, default=0.2)
    args = parser.parse_args()
    if args.limit < 1 or args.pause < 0:
        parser.error("--limit은 1 이상, --pause는 0 이상이어야 합니다.")
    calls, matched = collect(args.limit, args.pause)
    print(f"완료: 이번 실행 {calls}건 신규 조회. 줄거리 매칭 누적 {matched}편을 {OUTPUT_PATH}에 저장했습니다.")
