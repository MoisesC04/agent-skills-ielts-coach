"""Synthetic regression cases; no learner history is used."""
from copy import deepcopy
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coach", ROOT / "tools/coach.py")
coach = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach)


class ObjectiveMarking(unittest.TestCase):
    def setUp(self):
        self.key = json.loads((ROOT / "tests/fixtures/reading-key.json").read_text())

    def test_partial_practice_has_raw_score_and_no_band(self):
        answers = json.loads((ROOT / "tests/fixtures/reading-response.json").read_text())
        result = coach.score(self.key, answers)
        self.assertEqual((result["correct"], result["total"]), (3, 4))
        self.assertIsNone(result["band"])

    def test_word_limit_and_missing_answers(self):
        self.key["items"][3]["accepted"].append("in June")
        result = coach.score(self.key, {"4": "in June"})
        self.assertEqual(result["correct"], 0)
        self.assertFalse(result["items"][3]["within_word_limit"])

    def test_spelling_is_not_fuzzy(self):
        self.assertEqual(coach.score(self.key, {"4": "Juun"})["correct"], 0)

    def test_unverified_or_ambiguous_keys_are_rejected(self):
        for mutation in (lambda k: k.pop("source"), lambda k: k["items"].append(k["items"][0]),
                         lambda k: k["items"][0].update(accepted=[])):
            key = deepcopy(self.key)
            mutation(key)
            with self.assertRaises(ValueError):
                coach.score(key, {})
        with self.assertRaises(ValueError):
            coach.score(self.key, {"99": "TRUE"})


class ReviewQueue(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 1, 1)
        self.data = {"version": 1, "errors": []}
        self.error = coach.add_error(self.data, "writing", "Agreement", "It show.", "It shows.", self.today)

    def test_same_day_retry_does_not_establish_mastery(self):
        coach.review(self.error, "correct", "A new sentence.", self.today)
        self.assertEqual(self.error["independent_successes"], 0)
        self.assertEqual(self.error["next_due"], "2026-01-02")

    def test_assisted_attempt_does_not_advance(self):
        coach.review(self.error, "assisted", "A sentence after a hint.", self.today + timedelta(days=1))
        self.assertEqual(self.error["independent_successes"], 0)

    def test_delayed_successes_then_relapse(self):
        for day, next_due in [(2, "2026-01-05"), (5, "2026-01-12"), (12, "2026-01-26"), (26, "2026-02-25")]:
            coach.review(self.error, "correct", "Independent novel-context evidence.", date(2026, 1, day))
            self.assertEqual(self.error["next_due"], next_due)
        self.assertEqual(self.error["status"], "stabilized")
        coach.review(self.error, "incorrect", "A later independent error.", date(2026, 2, 25))
        self.assertEqual(self.error["independent_successes"], 0)
        self.assertEqual(self.error["next_due"], "2026-02-26")

    def test_recurring_pattern_reuses_id_and_resets(self):
        original_id = self.error["id"]
        again = coach.add_error(self.data, "writing", "agreement", "They is.", "They are.", self.today)
        self.assertEqual(again["id"], original_id)
        self.assertEqual(again["seen_count"], 2)
        self.assertEqual(again["status"], "recurring")
        self.assertEqual(len(self.data["errors"]), 1)

    def test_empty_or_backdated_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            coach.review(self.error, "correct", "", self.today)
        with self.assertRaises(ValueError):
            coach.review(self.error, "correct", "Evidence", self.today - timedelta(days=1))

    def test_no_history_is_read_only_and_records_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "private/progress.json"
            self.assertEqual(coach.read_queue(path), {"version": 1, "errors": []})
            self.assertFalse(path.exists())
            coach.save_queue(path, self.data)
            self.assertEqual(coach.read_queue(path), self.data)


if __name__ == "__main__":
    unittest.main()
