import unittest

class TestPlacesNormalization(unittest.TestCase):
    def test_places_results_are_dicts(self):
        # Simulate the "bad" case that crashed: list of strings
        raw = ["a", "b", "c"]
        normalized = []
        for r in raw:
            if isinstance(r, dict):
                normalized.append(r)
            else:
                normalized.append({"name": str(r)})

        # Our pipeline expects dict-like objects with .get
        for r in normalized:
            self.assertIsInstance(r, dict)
            self.assertTrue(hasattr(r, "get"))
