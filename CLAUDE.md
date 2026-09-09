# CLAUDE.md

이 저장소에서 작업할 때 참고할 내용.

## 명령

```bash
source .venv/Scripts/activate          # Windows Git Bash
pip install -r requirements.txt
python -m unittest test_recommender    # 테스트
python build_dataset.py                # 데이터 재생성 (형태소 분석이라 몇 분 걸림)
streamlit run app.py                   # 앱
python recommend.py --title 친구
```

## 구조

`kobis_catalog.json`(KOBIS 목록) + `overview_ko.json`(한국어 줄거리) →
`build_dataset.py` → `movies.json` + `tokens.json` → `recommender.py`(Kiwi + BM25) →
`app.py` / `recommend.py`.

추천 방식은 하나뿐이다. 임베딩·TF-IDF·벤치마크 스크립트는 모두 제거했다.
`recommender.document()`가 영화 한 편을 장르·제작국·감독·줄거리를 이어 붙인
글로 만들고, `tokenize()`가 Kiwi로 내용어만 남기며, `recommend()`가 고른 영화의
토큰을 질의로 삼아 BM25 점수를 매긴다.

## 알아 둘 점

- **줄거리는 27,852편 중 602편에만 있다.** OMDb를 영문 제목으로 조회해 얻은
  것을 한국어로 옮긴 결과다. 나머지는 `overview`가 빈 문자열이며 장르·제작국·
  감독만으로 비교된다. **후보군을 나누지 않는다.** 인덱스는 언제나 카탈로그
  전체 27,852편으로 한 번 짓는다.
- `data/overview_ko.json`은 손으로 다듬은 번역이라 저장소에 함께 둔다. 나머지
  `data/*.json`은 생성물이므로 gitignore 대상이다.
- KMDb 줄거리가 생기면 `data/overview_ko_kmdb.json`으로 저장하고
  `build_dataset.py`만 다시 돌린다. `OVERVIEW_PATHS`에서 뒤쪽이 앞쪽을 덮는다.
- `tokens.json`은 `movies.json`과 순서·길이가 정확히 같아야 한다. 어긋나면
  `recommend()`가 예외를 던진다. 그때는 `build_dataset.py`를 다시 실행한다.
