"""KOBIS 정보와 직접 작성한 줄거리·태그로 로컬 BM25 인덱스를 만든다."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from kobis import KOBISClient, KOBISError, movie_record

DATA_PATH = Path("data/movies.json")
DEFAULT_SOURCE = Path("data/curated_movies.json")

def build(source_path: Path) -> int:
    load_dotenv()
    if not source_path.exists():
        raise RuntimeError(f"{source_path} 파일이 없습니다. example 파일을 복사해 영화 정보를 입력하십시오.")
    try:
        curated = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError("큐레이션 파일은 올바른 JSON 배열이어야 합니다.") from error
    if not isinstance(curated, list):
        raise RuntimeError("큐레이션 파일의 최상위 값은 배열이어야 합니다.")
    client = KOBISClient(os.getenv("KOBIS_API_KEY", ""))
    movies = []
    for row in curated:
        if not isinstance(row, dict):
            raise RuntimeError("각 영화 항목은 객체여야 합니다.")
        movie_cd, overview = str(row.get("movie_cd", "")), row.get("overview", "")
        if not isinstance(overview, str) or not overview.strip():
            raise RuntimeError(f"{movie_cd or '알 수 없는 항목'}의 overview는 비어 있지 않은 문자열이어야 합니다.")
        record = movie_record(client.movie_details(movie_cd), overview, [])
        movies.append(record)
        print(f"{len(movies)}/{len(curated)}편 처리 완료: {record['title']}")
    if len(movies) < 2:
        raise RuntimeError("추천을 위해서는 최소 2편의 영화가 필요합니다.")
    DATA_PATH.parent.mkdir(exist_ok=True)
    temporary_path = DATA_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(movies, ensure_ascii=False), encoding="utf-8")
    temporary_path.replace(DATA_PATH)
    return len(movies)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOBIS 기반 영화 BM25 데이터 생성")
    parser.add_argument("--input", type=Path, default=DEFAULT_SOURCE, metavar="JSON")
    args = parser.parse_args()
    try:
        print(f"완료: {build(args.input)}편을 {DATA_PATH}에 저장했습니다.")
    except (KOBISError, RuntimeError) as error:
        raise SystemExit(f"오류: {error}")
