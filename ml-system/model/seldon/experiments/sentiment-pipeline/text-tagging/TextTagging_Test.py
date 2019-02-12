import unittest
import TextTagging


class TextTagging_Test(unittest.TestCase):
    def setUp(self):
        self.tagging = TextTagging.TextTagging()

    def test(self):
        params = [
            "The pigeonhole principle is a simple, yet beautiful and useful idea. Given a set A of pigeons and a set B of pigeonholes, if all the pigeons fly into a pigeonhole and there are more pigeons than holes, then one of the pigeonholes has to contain more than one pigeon."
        ]
        response = self.tagging.predict(
            params, "features", {'tags': {
                'sentiment_analysis_passed': True
            }})
        self.assertIsNotNone(response)


if __name__ == '__main__':
    unittest.main()
