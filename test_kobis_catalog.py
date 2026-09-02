import unittest

from kobis import catalog_record


class KOBISCatalogTest(unittest.TestCase):
    def test_normalizes_list_response(self):
        record = catalog_record({"movieCd": "1", "movieNm": "테스트", "genreAlt": "드라마,스릴러", "directors": [{"peopleNm": "감독"}]})
        self.assertEqual(record["genres"], ["드라마", "스릴러"])
        self.assertEqual(record["directors"], ["감독"])


if __name__ == "__main__":
    unittest.main()
