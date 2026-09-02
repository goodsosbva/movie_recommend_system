# 영화 유사 작품 추천

KOBIS의 영화 카탈로그를 사용합니다. 현재는 KOBIS가 제공하는 장르·제작국·감독·형식으로 전체 영화의 유사도를 계산합니다. TMDB API·로고·토큰은 사용하지 않습니다.

## 데이터 구조

- `data/kobis_catalog.json`: KOBIS에서 수집한 전체 검색 카탈로그
- `data/metadata_embeddings.npy`: 전체 카탈로그의 메타데이터 임베딩 행렬
- `data/metadata_embedding_ids.json`: 임베딩 행과 영화 ID의 대응표
- `reports/metadata_benchmark.md`: TF-IDF·BM25·문장 임베딩 기준선 비교 결과

KOBIS는 줄거리와 포스터를 주지 않습니다. 따라서 현재 추천은 **내용 유사도**가 아닌 **메타데이터 유사도**입니다. KMDb API 키가 발급되면 줄거리 기반 임베딩을 별도로 만들고, 같은 평가 기준으로 성능을 다시 비교합니다.

## 실행

```bash
cd /c/Users/admin/Desktop/side/movie_recommend
source .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
```

1. [KOBIS 오픈API](https://kobis.or.kr/kobisopenapi/homepg/main/main.do)에서 서비스 키를 발급해 `.env`의 `KOBIS_API_KEY`에 입력합니다.
2. 전체 카탈로그와 임베딩, 비교 보고서를 생성합니다.

```bash
python build_embeddings.py
python evaluate_recommenders.py
python -m unittest test_embedding.py test_recommender.py test_kobis.py test_kobis_catalog.py
streamlit run app.py
```

전체 KOBIS 카탈로그가 아직 없을 때만 아래 명령으로 수집합니다.

```bash
python build_kobis_catalog.py --start-year 2000
```

KMDb 줄거리 결합 후에는 `--source plot`으로 별도 임베딩 파일을 생성하고, `reports/metadata_benchmark.md`와 같은 기준으로 비교합니다. 개발 순서는 [개발 흐름 문서](docs/development-flow.md)에 정리했습니다.

실제 `.env`, API에서 수집한 대용량 카탈로그와 임베딩 파일은 Git에 올리지 않습니다.
