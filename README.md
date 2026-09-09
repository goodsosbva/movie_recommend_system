# 영화 추천 (KOBIS + 한국어 줄거리 + BM25)

KOBIS에서 모은 영화 목록에 한국어 줄거리를 붙이고, 형태소 분석과 BM25 유사도로
"방금 본 영화와 비슷한 작품"을 찾아 준다.

## 어떻게 동작하는가

영화 한 편을 아래처럼 한 덩어리 글로 만든다.

```
드라마
한국
곽경택
어릴 적 친구 넷이 각자의 길을 간다. 둘은 대학에 가고 나머지 둘은 서로 다른 조직의 건달이 된다.
```

이 글을 Kiwi로 형태소 분석해 명사·동사·형용사만 남긴다. 조사와 어미는 버린다.
그러면 영화 한 편이 낱말 목록이 되고, 카탈로그 전체가 낱말 목록의 모음이 된다.

추천은 **고른 영화의 낱말 목록을 그대로 검색어로 삼아 나머지를 검색하는 것**이다.
BM25는 검색 점수 계산법이다. 드문 낱말이 겹칠수록 점수를 크게 주고, 같은 낱말이
여러 번 나와도 점수가 끝없이 커지지 않게 눌러 주며, 글이 긴 영화가 유리해지지
않도록 길이를 보정한다. 점수가 높은 순으로 돌려주면 그것이 추천 목록이다.

`장르`나 `감독`은 여러 영화에 흔히 나오므로 점수를 조금만 올리고, 줄거리에만
나오는 낱말(`권투`, `우주선`, `탈옥`)은 드물기 때문에 점수를 크게 올린다.
따로 가중치를 정하지 않아도 BM25가 알아서 그렇게 계산한다.

## 데이터 만들기

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt

python build_kobis_catalog.py --start-year 2000   # .env에 KOBIS_API_KEY 필요
python build_omdb_overviews.py                    # .env에 OMDB_API_KEY 필요 (선택)
python build_dataset.py                           # 합치고 형태소 토큰까지 저장
```

| 파일 | 내용 |
|---|---|
| `data/kobis_catalog.json` | KOBIS 영화 목록 (27,852편) |
| `data/omdb_overview_cache.json` | OMDb 영문 줄거리 원본 |
| `data/overview_ko.json` | **한국어 줄거리 602편.** `{영화코드: 줄거리}` |
| `data/movies.json` | 위를 합친 결과 |
| `data/tokens.json` | 영화별 형태소 토큰 (앱 시작을 빠르게 하는 캐시) |

## 쓰기

```bash
streamlit run app.py                       # 화면
python recommend.py --title 친구 --only-plot  # 터미널
```

`--only-plot`(화면에서는 "줄거리 있는 작품끼리만 비교")을 켜면 줄거리가 있는
602편 안에서만 비교한다. 끄면 27,852편 전체가 대상이 되지만, 줄거리가 없는
영화는 장르·제작국·감독만으로 비교된다.

## KMDb 줄거리를 붙일 때

`data/overview_ko_kmdb.json`을 `{영화코드: 한국어 줄거리}` 형식으로 만들어
`data/`에 두고 `python build_dataset.py`를 다시 실행하면 된다. 코드는 고치지
않는다. 같은 영화가 양쪽에 있으면 KMDb 쪽이 이긴다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `kobis.py` | KOBIS 오픈API 호출 |
| `build_kobis_catalog.py` | 연도별 영화 목록 수집 |
| `build_omdb_overviews.py` | OMDb 영문 줄거리 수집 (하루 1,000건 제한) |
| `build_dataset.py` | 카탈로그 + 줄거리 병합, 형태소 토큰 생성 |
| `recommender.py` | 토큰화 · 문서 구성 · BM25 인덱스 · 추천 |
| `app.py` | Streamlit 화면 |
| `recommend.py` | 터미널 확인용 |
| `test_recommender.py` | 단위 테스트 (`python -m unittest test_recommender`) |
