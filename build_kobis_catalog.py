"""KOBIS 영화 목록을 연도별로 수집해 로컬 카탈로그를 만든다."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from kobis import KOBISClient, KOBISError, catalog_record


CATALOG_PATH = Path("data/kobis_catalog.json")


def save(records: dict[str, dict]) -> None:
    CATALOG_PATH.parent.mkdir(exist_ok=True)
    temporary = CATALOG_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(list(records.values()), ensure_ascii=False), encoding="utf-8")
    temporary.replace(CATALOG_PATH)


def collect(start_year: int, end_year: int, pause: float) -> int:
    load_dotenv()
    client = KOBISClient(os.getenv("KOBIS_API_KEY", ""))
    records = {row["id"]: row for row in json.loads(CATALOG_PATH.read_text(encoding="utf-8"))} if CATALOG_PATH.exists() else {}
    for year in range(start_year, end_year + 1):
        first = client.movie_list(year, 1)
        total = int(first.get("totCnt", 0))
        pages = max(1, (total + 99) // 100)
        for page in range(1, pages + 1):
            result = first if page == 1 else client.movie_list(year, page)
            for movie in result.get("movieList", []):
                record = catalog_record(movie)
                records[record["id"]] = record
            print(f"{year}년 {page}/{pages} 페이지: 누적 {len(records):,}편")
            if page < pages:
                time.sleep(pause)
        save(records)
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOBIS 대량 영화 카탈로그 수집")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=date.today().year)
    parser.add_argument("--pause", type=float, default=0.1)
    args = parser.parse_args()
    if not 1900 <= args.start_year <= args.end_year <= date.today().year:
        parser.error("연도 범위가 올바르지 않습니다.")
    if args.pause < 0:
        parser.error("--pause은 0 이상이어야 합니다.")
    try:
        print(f"완료: {collect(args.start_year, args.end_year, args.pause):,}편을 {CATALOG_PATH}에 저장했습니다.")
    except KOBISError as error:
        raise SystemExit(f"오류: {error}")
