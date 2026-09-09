import unittest

from recommender import build_index, common_terms, document, recommend, tokenize

MOVIES = [
    {"id": "1", "title": "우주 표류", "year": "2014", "nation": "미국", "genres": ["SF"],
     "directors": ["김감독"], "overview": "고장 난 우주선에 홀로 남은 우주 비행사가 지구로 돌아갈 길을 찾는다."},
    {"id": "2", "title": "화성 생존기", "year": "2015", "nation": "미국", "genres": ["SF"],
     "directors": ["이감독"], "overview": "화성에 홀로 남겨진 우주 비행사가 구조를 기다리며 살아남는다."},
    {"id": "3", "title": "시골 밥상", "year": "2016", "nation": "한국", "genres": ["다큐멘터리"],
     "directors": ["박감독"], "overview": "산골 마을 할머니가 제철 나물로 밥상을 차린다."},
]


class RecommenderTest(unittest.TestCase):
    def setUp(self):
        self.tokens = [tokenize(document(movie)) for movie in MOVIES]
        self.index = build_index(self.tokens)

    def test_tokenize_drops_particles(self):
        self.assertNotIn("가", tokenize("우주 비행사가 돌아간다"))

    def test_document_includes_overview_and_metadata(self):
        text = document(MOVIES[0])
        self.assertIn("SF", text)
        self.assertIn("우주 비행사", text)

    def test_recommends_same_subject_first_and_excludes_self(self):
        results = recommend(self.index, self.tokens, MOVIES, 0, limit=2)
        self.assertEqual(results[0]["movie"]["id"], "2")
        self.assertNotIn("1", [item["movie"]["id"] for item in results])

    def test_reports_common_terms(self):
        results = recommend(self.index, self.tokens, MOVIES, 0, limit=1)
        self.assertIn("우주", results[0]["terms"])

    def test_common_terms_keeps_query_order_without_duplicates(self):
        self.assertEqual(common_terms(["가", "나", "가", "다"], ["다", "가"]), ["가", "다"])

    def test_rejects_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            recommend(self.index, self.tokens[:2], MOVIES, 0)


if __name__ == "__main__":
    unittest.main()
