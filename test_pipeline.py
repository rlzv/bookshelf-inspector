import unittest
import pandas as pd
from pipeline import adjusted_score, country, normalize, shortlist, rank


class RankingTests(unittest.TestCase):
    def test_small_sample_is_shrunk_more(self):
        self.assertLess(adjusted_score(10, 1, 7, 50), adjusted_score(9, 100, 7, 50))

    def test_mean_equal_to_prior_is_unchanged(self):
        self.assertEqual(adjusted_score(7, 123, 7, 50), 7)

    def test_unknown_country_is_not_evidence(self):
        self.assertTrue(pd.isna(country('somewhere, not-a-country')))
        self.assertEqual(country('Prague, region, Czech Republic'), 'czechia')

    def test_normalization(self):
        self.assertEqual(normalize('  A  Title  '), normalize('a title'))

    def test_author_cap(self):
        frame = pd.DataFrame({'author_key': ['a', 'a', 'a', 'b']})
        self.assertEqual(list(shortlist(frame, n=3).index), [0, 1, 3])

    def test_rank_favours_supported_quality(self):
        frame = pd.DataFrame({'work': ['a'] + ['b'] * 100,
                              'user_id': range(101), 'rating': [10] + [9] * 100})
        self.assertEqual(rank(frame, 'work', 7, 50).index[0], 'b')


if __name__ == '__main__':
    unittest.main()
