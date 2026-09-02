import unittest

from recommender import build_bm25, recommend


def movie(movie_id, tokens, genres, keywords, director=None, casts=None, adult=False):
    return {
        "id": movie_id,
        "title": str(movie_id),
        "year": "2020",
        "overview": "",
        "tokens": tokens,
        "genre_ids": genres,
        "keyword_ids": keywords,
        "director_id": director,
        "cast_ids": casts or [],
    }


class RecommendationTest(unittest.TestCase):
    def test_excludes_selected_movie_and_ranks_related_movie_first(self):
        selected = movie(1, ["우주", "생존", "탐사"], [878], [1], 10, [20])
        related = movie(2, ["우주", "생존", "행성"], [878], [1], 10, [21])
        unrelated = movie(3, ["사랑", "음악", "무대"], [10402], [2])
        movies = [selected, related, unrelated]
        result = recommend(selected, movies, build_bm25(movies), limit=2)
        self.assertEqual(result[0]["movie"]["id"], 2)
        self.assertNotIn(1, [item["movie"]["id"] for item in result])

    def test_keeps_adult_movies_in_recommendations(self):
        selected = movie(1, ["공포", "호텔"], [27], [1])
        adult_related = movie(2, ["공포", "호텔"], [27], [1], adult=True)
        movies = [selected, adult_related]

        result = recommend(selected, movies, build_bm25(movies), limit=1)

        self.assertEqual(result[0]["movie"]["id"], 2)


if __name__ == "__main__":
    unittest.main()
