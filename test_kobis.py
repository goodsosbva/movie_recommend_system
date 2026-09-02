import unittest

from kobis import movie_record


class KOBISRecordTest(unittest.TestCase):
    def test_combines_kobis_metadata_with_our_text(self):
        info = {"movieCd": "20240001", "movieNm": "테스트", "prdtYear": "2024", "genres": [{"genreNm": "드라마"}], "directors": [{"peopleNm": "감독"}], "actors": [{"peopleNm": "배우"}], "audits": []}
        record = movie_record(info, "직접 작성한 줄거리", ["성장"])
        self.assertEqual(record["genre_ids"], ["드라마"])
        self.assertEqual(record["keyword_ids"], ["성장"])
        self.assertEqual(record["director_id"], "감독")


if __name__ == "__main__":
    unittest.main()
