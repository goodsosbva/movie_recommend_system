"""같은 카탈로그·같은 입력 텍스트로 TF-IDF, BM25, 임베딩의 검색 품질 기준선을 만든다."""
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

SOURCE_DESCRIPTION = {
    "metadata": "KOBIS 장르·제작국·감독·형식. 제목과 줄거리는 입력하지 않음.",
    "plot": "줄거리와 장르. 줄거리가 확보된 작품만 대상.",
    "combined": "장르·제작국·감독·형식에 줄거리가 있으면 덧붙임.",
}


def ranks_without_self(ranked: list[int], selected: int, limit: int) -> list[int]:
    return [index for index in ranked if index != selected][:limit]


def build_documents(movies: list[dict], source: str) -> list[str]:
    """세 방식이 모두 같은 텍스트를 입력받도록 한 곳에서 만든다."""
    return [movie_text(movie, source) for movie in movies]


def main() -> None:
    parser = argparse.ArgumentParser(description="추천 방식 기준선 평가")
    parser.add_argument("--catalog", type=Path, default=Path("data/kobis_catalog.json"))
    parser.add_argument("--embeddings", type=Path, default=Path("data/metadata_embeddings.npy"))
    parser.add_argument("--ids", type=Path, default=Path("data/metadata_embedding_ids.json"))
    parser.add_argument("--source", choices=tuple(SOURCE_DESCRIPTION), default="metadata",
                        help="TF-IDF·BM25·임베딩이 공통으로 쓸 입력 텍스트. --embeddings를 만들 때 준 --source와 같아야 한다.")
    parser.add_argument("--queries", type=int, default=100)
    parser.add_argument("--report", type=Path, default=None, metavar="MD",
                        help="기본값은 reports/<source>_benchmark.md")
    args = parser.parse_args()
    report_path = args.report or Path(f"reports/{args.source}_benchmark.md")

    movies = json.loads(args.catalog.read_text(encoding="utf-8"))
    ids = json.loads(args.ids.read_text(encoding="utf-8"))
    embeddings = np.load(args.embeddings)
    if [str(movie["id"]) for movie in movies] != ids or len(movies) != len(embeddings):
        raise SystemExit("오류: 카탈로그와 임베딩 인덱스가 일치하지 않습니다. build_embeddings.py를 다시 실행하십시오.")
    eligible = [index for index, movie in enumerate(movies) if movie.get("genres")]
    if len(eligible) < 2:
        raise SystemExit("오류: 장르가 있는 영화가 최소 2편 필요합니다.")
    queries = random.Random(42).sample(eligible, min(args.queries, len(eligible)))
    try:
        documents = build_documents(movies, args.source)
    except ValueError as error:
        raise SystemExit(f"오류: {error} (--source {args.source}에 맞지 않는 카탈로그입니다.)")
    with_overview = sum(1 for movie in movies if str(movie.get("overview", "")).strip())

    vectorizer = TfidfVectorizer(tokenizer=tokenize, token_pattern=None)
    tfidf = vectorizer.fit_transform(documents)
    bm25 = build_bm25(documents)
    methods = {"TF-IDF": [], "BM25": [], "문장 임베딩": []}
    for selected in queries:
        methods["TF-IDF"].append(ranks_without_self(list((tfidf @ tfidf[selected].T).toarray().ravel().argsort()[::-1]), selected, 10))
        methods["BM25"].append(ranks_without_self(bm25_rank(bm25, documents[selected]), selected, 10))
        methods["문장 임베딩"].append(ranks_without_self(list((embeddings @ embeddings[selected]).argsort()[::-1]), selected, 10))
    lines = [
        f"# 추천 기준선 — {args.source}", "",
        f"- 입력 텍스트: **{args.source}** — {SOURCE_DESCRIPTION[args.source]}",
        "- 세 방식 모두 위 텍스트를 그대로 입력한다. 방식 간 입력 차이는 없다.",
        f"- 카탈로그: `{args.catalog}` ({len(movies):,}편, 줄거리 보유 {with_overview:,}편)",
        f"- 임베딩: `{args.embeddings}`",
        f"- 평가 질의: {len(queries)}편 (고정 난수 시드 42)",
        "- 정답 기준: 추천 영화가 기준 영화와 장르를 하나 이상 공유하면 관련으로 계산.",
        "", "| 방식 | Precision@10 | nDCG@10 | 후보 다양성@10 |", "|---|---:|---:|---:|",
    ]
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
    lines += [
        "", "## 읽는 법", "",
        "정답을 “장르를 하나 이상 공유하는가”로 정의했다. 따라서 이 표는 **장르를 얼마나 일관되게 재현하는지**를 재는 것이지, 영화 내용이 비슷한지를 재는 것이 아니다.",
        "장르를 직접 입력받는 `metadata`가 유리하고, 장르 대신 사건을 담은 `plot`은 같은 잣대에서 낮게 나오는 것이 정상이다.",
        "**서로 다른 `--source`의 표를 가로질러 비교하지 말 것.** 같은 표 안에서 세 방식을 비교하는 용도다.",
    ]
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"완료: {report_path}에 {args.source} 입력으로 {len(queries)}개 질의를 평가한 결과를 저장했습니다.")


if __name__ == "__main__":
    main()
