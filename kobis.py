"""KOBIS 영화 상세 정보를 추천 데이터 형태로 정규화한다."""

from __future__ import annotations

from typing import Any

import requests


BASE_URL = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/movie"


class KOBISError(RuntimeError):
    """KOBIS 요청 또는 입력 데이터가 잘못됐을 때의 안전한 오류."""


class KOBISClient:
    def __init__(self, key: str) -> None:
        if not key or key.startswith("replace_"):
            raise KOBISError("KOBIS_API_KEY 환경변수를 설정하십시오.")
        self.key = key
        self.session = requests.Session()

    def movie_details(self, movie_cd: str) -> dict[str, Any]:
        if not movie_cd.isdigit():
            raise KOBISError("movie_cd는 KOBIS 영화 코드 숫자여야 합니다.")
        try:
            response = self.session.get(
                f"{BASE_URL}/searchMovieInfo.json",
                params={"key": self.key, "movieCd": movie_cd},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            raise KOBISError("KOBIS에서 영화 정보를 가져오지 못했습니다. 잠시 후 다시 시도하십시오.") from error
        info = data.get("movieInfoResult", {}).get("movieInfo")
        if not info:
            raise KOBISError(f"KOBIS 영화 코드 {movie_cd}의 정보를 찾지 못했습니다.")
        return info

    def movie_list(self, year: int, page: int) -> dict[str, Any]:
        if not 1900 <= year <= 2100 or page < 1:
            raise KOBISError("영화 목록 조회 연도 또는 페이지가 올바르지 않습니다.")
        try:
            response = self.session.get(
                f"{BASE_URL}/searchMovieList.json",
                params={"key": self.key, "openStartDt": str(year), "openEndDt": str(year), "curPage": page, "itemPerPage": 100},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as error:
            raise KOBISError("KOBIS에서 영화 목록을 가져오지 못했습니다. 잠시 후 다시 시도하십시오.") from error
        result = data.get("movieListResult")
        if not result:
            message = data.get("faultInfo", {}).get("message", "알 수 없는 오류")
            raise KOBISError(f"KOBIS 영화 목록 오류: {message}")
        return result


def catalog_record(summary: dict[str, Any]) -> dict[str, Any]:
    """목록 API 응답을 검색용 카탈로그 레코드로 바꾼다."""
    return {
        "id": summary["movieCd"],
        "title": summary.get("movieNm") or "제목 없음",
        "original_title": summary.get("movieNmEn") or "",
        "year": summary.get("prdtYear") or "",
        "release_date": summary.get("openDt") or "",
        "type": summary.get("typeNm") or "",
        "status": summary.get("prdtStatNm") or "",
        "nation": summary.get("repNationNm") or "",
        "genres": [genre for genre in (summary.get("genreAlt") or "").split(",") if genre],
        "directors": [person["peopleNm"] for person in summary.get("directors", []) if person.get("peopleNm")],
    }


def movie_record(info: dict[str, Any], overview: str, tags: list[str]) -> dict[str, Any]:
    """KOBIS 응답과 직접 작성한 추천 텍스트를 하나의 영화 레코드로 합친다."""
    genres = [item["genreNm"] for item in info.get("genres", []) if item.get("genreNm")]
    directors = [item["peopleNm"] for item in info.get("directors", []) if item.get("peopleNm")]
    actors = [item["peopleNm"] for item in info.get("actors", []) if item.get("peopleNm")][:5]
    return {
        "id": info["movieCd"],
        "title": info.get("movieNm") or "제목 없음",
        "year": info.get("prdtYear") or "",
        "overview": overview.strip(),
        "genre_ids": genres,
        "keyword_ids": [tag.strip() for tag in tags if tag.strip()],
        "director_id": directors[0] if directors else None,
        "cast_ids": actors,
        "genres": genres,
        "directors": directors,
        "actors": actors,
        "watch_grade": ", ".join(item["watchGradeNm"] for item in info.get("audits", []) if item.get("watchGradeNm")),
    }
