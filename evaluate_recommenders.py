"""같은 KOBIS 카탈로그에서 TF-IDF, BM25, 임베딩의 검색 품질 기준선을 만든다."""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from recommenders.bm25.recommender import build as build_bm25, rank as bm25_rank, tokenize
from recommenders.embedding.recommender import movie_text


def ranks_without_self(ranked: list[int], selected: int, limit: int) -> list[int]:
    return [index for index in ranked if index != selected][:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="KOBIS 메타데이터 추천 기준선 평가")
    parser.add_argument("--catalog", type=Path, default=Path("data/kobis_catalog.json"))
    parser.add_argument("--embeddings", type=Path, default=Path("data/metadata_embeddings.npy"))
    parser.add_argument("--ids", type=Path, default=Path("data/metadata_embedding_ids.json"))
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--report", type=Path, default=Path("reports/metadata_benchmark.md"))
    args = parser.parse_args()
    movies = json.loads(args.catalog.read_text(encoding="utf-8"))
    ids = json.loads(args.ids.read_text(encoding="utf-8"))
    embeddings = np.load(args.embeddings)
    if [str(movie["id"]) for movie in movies] != ids or len(movies) != len(embeddings):
        raise SystemExit("오류: 카탈로그와 임베딩 인덱스가 일치하지 않습니다. build_embeddings.py를 다시 실행하십시오.")
    eligible = [index for index, movie in enumerate(movies) if movie.get("genres")]
    if len(eligible) < 2:
        raise SystemExit("오류: 장르가 있는 영화가 최소 2편 필요합니다.")
    queries = random.Random(42).sample(eligible, min(args.queries, len(eligible)))
    documents = [movie_text(movie) for movie in movies]
    vectorizer = TfidfVectorizer(tokenizer=tokenize, token_pattern=None)
    tfidf = vectorizer.fit_transform(documents)
    bm25 = build_bm25(documents)
    methods = {"TF-IDF": [], "BM25": [], "문장 임베딩": []}
    for selected in queries:
        methods["TF-IDF"].append(ranks_without_self(list((tfidf @ tfidf[selected].T).toarray().ravel().argsort()[::-1]), selected, 10))
        methods["BM25"].append(ranks_without_self(bm25_rank(bm25, documents[selected]), selected, 10))
        methods["문장 임베딩"].append(ranks_without_self(list((embeddings @ embeddings[selected]).argsort()[::-1]), selected, 10))
    lines = [
        "# KOBIS 메타데이터 추천 기준선", "",
        f"- 평가 일시: 자동 생성", f"- 후보 영화: {len(movies):,}편", f"- 평가 질의: {len(queries)}편 (고정 난수 시드 42)",
        "- 입력: KOBIS 장르·제작국·감독·형식. 제목과 줄거리는 입력하지 않음.",
        "- 정답 기준: 추천 영화가 기준 영화와 장르를 하나 이상 공유하면 관련으로 계산.",
        "", "| 방식 | Precision@10 | nDCG@10 | 후보 다양성@10 |", "|---|---:|---:|---:|",
    ]
    # 질의별 기준 영화가 전체 카탈로그에 있으므로 메트릭 계산을 바로 수행한다.
    for name, all_ranked in methods.items():
        precision, ndcg, unique = [], [], set()
        for selected, ranked in zip(queries, all_ranked):
            genres = set(movies[selected]["genres"])
            gains = [bool(genres & set(movies[index].get("genres", []))) for index in ranked]
            precision.append(sum(gains) / 10)
            dcg = sum(gain / math.log2(position + 2) for position, gain in enumerate(gains))
            ideal = sum(1 / math.log2(position + 2) for position in range(10))
            ndcg.append(dcg / ideal)
            unique.update(ranked)
        values = (100 * sum(precision) / len(precision), 100 * sum(ndcg) / len(ndcg), 100 * len(unique) / (len(queries) * 10))
        lines.append(f"| {name} | {values[0]:.2f}% | {values[1]:.2f}% | {values[2]:.2f}% |")
    lines += ["", "## 해석", "", "이 결과는 **줄거리 유사도 성능이 아니다**. 현재 KOBIS에 있는 메타데이터만으로 같은 장르를 얼마나 잘 묶는지 보는 기준선이다.", "KMDb 줄거리 결합 후에는 같은 질의·후보군·Precision@10·nDCG@10·다양성@10을 유지한 채, 줄거리 임베딩 결과를 추가해 전후 수치를 비교한다."]
    args.report.parent.mkdir(exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"완료: {args.report}에 {len(queries)}개 질의의 비교 결과를 저장했습니다.")


if __name__ == "__main__":
    main()
