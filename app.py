"""KOBIS 메타데이터 임베딩으로 비슷한 영화를 추천한다."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import streamlit as st
from recommenders.embedding.recommender import recommend

CATALOG_PATH = Path("data/kobis_catalog.json")
EMBEDDINGS_PATH = Path("data/metadata_embeddings.npy")
IDS_PATH = Path("data/metadata_embedding_ids.json")


@st.cache_data
def load_catalog() -> list[dict]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8")) if CATALOG_PATH.exists() else []

@st.cache_resource
def load_embeddings() -> tuple[list[str], np.ndarray]:
    return json.loads(IDS_PATH.read_text(encoding="utf-8")), np.load(EMBEDDINGS_PATH)

def main() -> None:
    st.set_page_config(page_title="영화 추천", page_icon="🎬", layout="wide")
    st.title("🎬 방금 본 영화와 비슷한 작품")
    st.write("현재는 KOBIS의 장르·제작국·감독·형식으로 추천합니다. KMDb 줄거리 결합 뒤 내용 유사도와 비교합니다.")
    catalog = load_catalog()
    if not catalog:
        st.warning("영화 카탈로그가 없습니다. `python build_kobis_catalog.py --start-year 2000`을 실행하십시오.")
        return
    query = st.text_input("본 영화 제목", max_chars=100, placeholder="예: 인터스텔라")
    matches = [movie for movie in catalog if query.strip() and query.strip().casefold() in movie["title"].casefold()][:50]
    if query and not matches:
        st.info("저장된 영화 중 제목이 일치하는 작품이 없습니다.")
    if matches:
        chosen = st.selectbox("정확한 영화를 선택하십시오.", matches, format_func=lambda movie: f"{movie['title']} ({movie['year'] or '연도 미상'}) · {', '.join(movie.get('genres', [])) or '장르 미상'}")
        if st.button("이 영화를 봤어요", type="primary"):
            if not EMBEDDINGS_PATH.exists() or not IDS_PATH.exists():
                st.warning("임베딩 인덱스가 없습니다. `python build_embeddings.py`를 실행하십시오.")
            else:
                st.session_state["selected"] = chosen
                ids, embeddings = load_embeddings()
                st.session_state["recommendations"] = recommend(chosen, catalog, ids, embeddings)
    selected, recommendations = st.session_state.get("selected"), st.session_state.get("recommendations")
    if selected and recommendations is not None:
        st.subheader(f"{selected['title']}을(를) 본 뒤 추천하는 작품")
        for item in recommendations:
            movie = item["movie"]
            st.markdown(f"### {movie['title']} ({movie['year'] or '연도 미상'})")
            st.caption(" · ".join(movie.get("genres", [])) or "장르 정보 없음")
            if movie.get("directors"):
                st.caption(f"감독: {', '.join(movie['directors'])}")
            st.write(f"메타데이터 유사도: {item['score']:.3f}")

if __name__ == "__main__":
    main()
