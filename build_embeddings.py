"""KOBIS 카탈로그 또는 줄거리 결합 데이터를 문장 임베딩 행렬로 변환한다."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from recommenders.embedding.recommender import movie_text

CATALOG_PATH = Path("data/kobis_catalog.json")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def build(data_path: Path, embeddings_path: Path, ids_path: Path, source: str) -> int:
    movies = json.loads(data_path.read_text(encoding="utf-8"))
    if len(movies) < 2:
        raise RuntimeError("최소 2편의 영화 데이터가 필요합니다.")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode([movie_text(movie, source) for movie in movies], batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    embeddings_path.parent.mkdir(exist_ok=True)
    np.save(embeddings_path, embeddings)
    ids_path.write_text(json.dumps([str(movie["id"]) for movie in movies]), encoding="utf-8")
    return len(movies)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="영화 문장 임베딩 생성")
    parser.add_argument("--input", type=Path, default=CATALOG_PATH, metavar="JSON")
    parser.add_argument("--source", choices=("metadata", "plot"), default="metadata")
    parser.add_argument("--output", type=Path, default=Path("data/metadata_embeddings.npy"), metavar="NPY")
    parser.add_argument("--ids-output", type=Path, default=Path("data/metadata_embedding_ids.json"), metavar="JSON")
    args = parser.parse_args()
    try:
        count = build(args.input, args.output, args.ids_output, args.source)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        raise SystemExit(f"오류: {error}")
    print(f"완료: {count}편 {args.source} 임베딩을 {args.output}에 저장했습니다.")
