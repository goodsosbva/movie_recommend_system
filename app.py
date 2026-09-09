"""BM25로 비슷한 영화를 추천하는 화면.

카탈로그 전체를 하나의 후보군으로 쓴다. 줄거리가 있으면 문서에 들어가고
없으면 장르·제작국·감독만으로 문서가 만들어진다. 나누어 계산하지 않는다.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from recommender import build_index, recommend

MOVIES_PATH = Path("data/movies.json")
TOKENS_PATH = Path("data/tokens.json")


@st.cache_data(show_spinner=False)
def load_data() -> tuple[list[dict], list[list[str]]]:
    movies = json.loads(MOVIES_PATH.read_text(encoding="utf-8"))
    tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    if len(movies) != len(tokens):
        raise ValueError("movies.json과 tokens.json의 길이가 다릅니다. build_dataset.py를 다시 실행하십시오.")
    return movies, tokens


@st.cache_resource(show_spinner="BM25 인덱스를 만드는 중입니다...")
def load_index():
    """카탈로그 전체로 인덱스를 한 번 짓는다."""
    _, tokens = load_data()
    return build_index(tokens)


def main() -> None:
    st.set_page_config(page_title="영화 추천", page_icon="🎬", layout="centered")
    st.title("🎬 방금 본 영화와 비슷한 작품")

    if not MOVIES_PATH.exists() or not TOKENS_PATH.exists():
        st.error("데이터가 없습니다. 아래 명령을 먼저 실행하십시오.")
        st.code("python build_dataset.py", language="bash")
        return

    movies, tokens = load_data()
    index = load_index()
    with_plot = sum(1 for movie in movies if movie.get("overview"))
    with st.sidebar:
        st.header("설정")
        limit = st.slider("추천 편수", 3, 20, 10)
        st.caption(f"후보 {len(movies):,}편 (줄거리 보유 {with_plot:,}편)")
        st.caption("장르·제작국·감독에 줄거리가 있으면 덧붙여 형태소로 쪼갠 뒤 BM25로 순위를 매깁니다.")

    st.write(f"**{len(movies):,}편** 전체에서 추천합니다. 줄거리가 있는 작품은 줄거리까지 함께 비교합니다.")

    query = st.text_input("본 영화 제목", max_chars=100, placeholder="예: 친구")
    keyword = query.strip().casefold()
    matches = [movie for movie in movies if keyword in movie["title"].casefold()][:50] if keyword else []
    if keyword and not matches:
        st.info("제목이 일치하는 작품이 없습니다.")
        return
    if not matches:
        return

    chosen = st.selectbox(
        "정확한 영화를 선택하십시오.",
        matches,
        format_func=lambda movie: f"{movie['title']} ({movie['year'] or '연도 미상'}) · "
                                  f"{', '.join(movie.get('genres', [])) or '장르 미상'}"
                                  f"{' · 줄거리 있음' if movie.get('overview') else ''}",
    )
    if st.button("이 영화를 봤어요", type="primary"):
        st.session_state["selected_id"] = chosen["id"]

    selected_id = st.session_state.get("selected_id")
    if selected_id is None:
        return
    position = next((i for i, movie in enumerate(movies) if movie["id"] == selected_id), None)
    if position is None:
        st.warning("선택한 영화를 찾지 못했습니다. 다시 골라 주십시오.")
        return

    base = movies[position]
    st.divider()
    st.subheader(f"{base['title']}을(를) 본 뒤 추천하는 작품")
    st.caption(base.get("overview") or "이 영화에는 줄거리 정보가 없어 장르·제작국·감독으로만 비교합니다.")
    try:
        results = recommend(index, tokens, movies, position, limit)
    except ValueError as error:
        st.warning(str(error))
        return
    for item in results:
        movie = item["movie"]
        st.markdown(f"**{movie['title']}** ({movie['year'] or '연도 미상'})")
        st.caption(" · ".join(filter(None, (
            ", ".join(movie.get("genres", [])) or "장르 미상",
            movie.get("nation", ""),
            ", ".join(movie.get("directors", [])),
        ))))
        if movie.get("overview"):
            st.caption(movie["overview"])
        st.progress(item["ratio"], text=f"유사도 {item['ratio']:.0%} · 공통 낱말: {', '.join(item['terms']) or '없음'}")
        st.divider()


if __name__ == "__main__":
    main()
