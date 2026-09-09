import unittest

from recommenders.embedding.recommender import movie_text


class EmbeddingTextTest(unittest.TestCase):
    def test_metadata_does_not_use_title_or_missing_plot(self):
        text = movie_text({"title": "테스트", "genres": ["SF"], "nation": "미국", "directors": ["감독"], "type": "장편"})
        self.assertIn("장르: SF", text)
        self.assertNotIn("테스트", text)


if __name__ == "__main__":
    unittest.main()
