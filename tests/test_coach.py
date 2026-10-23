"""Synthetic regression cases; no learner history is used."""
from copy import deepcopy
from datetime import date, timedelta
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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
            self.assertEqual(coach.read_queue(path), {"version": 1, "errors": [], "vocabulary": []})
            self.assertFalse(path.exists())
            coach.save_queue(path, self.data)
            self.assertEqual(coach.read_queue(path), {**self.data, "vocabulary": []})


class VocabularyQueue(unittest.TestCase):
    def setUp(self):
        self.data = {"version": 1, "errors": [], "vocabulary": []}
        self.seed = json.loads((ROOT / "tests/fixtures/vocabulary-item.json").read_text())
        self.item = coach.add_vocabulary(self.data, **self.seed, today=date(2026, 1, 1))

    def retrieve(self, day, mode, outcome="correct", context=None):
        return coach.review_vocabulary(self.item, mode, outcome,
                                       context or f"New synthetic prompt and response on day {day}",
                                       date(2026, 1, day))

    def test_recognition_alone_never_establishes_retention(self):
        for day in (2, 5, 12, 26):
            self.retrieve(day, "recognition")
        self.assertEqual(self.item["status"], "recognized")
        self.assertEqual(self.item["successes_by_mode"]["production"], 0)
        self.assertEqual(self.item["next_due"], "2026-02-09")

    def test_retention_requires_delayed_original_production(self):
        for day, mode in ((2, "recognition"), (5, "production"), (12, "recognition"), (26, "production")):
            self.retrieve(day, mode)
        self.assertEqual(self.item["status"], "retained")
        self.assertEqual(self.item["next_due"], "2026-02-25")
        coach.review_vocabulary(self.item, "production", "incorrect", "A later failed response", date(2026, 2, 25))
        self.assertEqual(self.item["status"], "learning")
        self.assertEqual(self.item["independent_successes"], 0)
        self.assertEqual(self.item["successes_by_mode"]["production"], 0)
        self.assertEqual(self.item["next_due"], "2026-02-26")

    def test_same_day_hints_and_repeated_context_do_not_advance(self):
        self.retrieve(1, "production")
        self.retrieve(2, "production", "assisted")
        self.assertEqual(self.item["independent_successes"], 0)
        self.retrieve(3, "production", context="Independent answer in a particular context")
        self.retrieve(6, "production", context="Independent answer in a particular context")
        self.assertEqual(self.item["independent_successes"], 1)
        self.assertFalse(self.item["events"][-1]["independent"])

    def test_encounters_preserve_id_and_due_date_but_senses_are_separate(self):
        self.retrieve(2, "production")
        again = coach.add_vocabulary(self.data, **self.seed, today=date(2026, 1, 3))
        self.assertEqual(again["id"], self.item["id"])
        self.assertEqual(again["next_due"], "2026-01-05")
        self.assertEqual(again["status"], "usable")
        alternate = {**self.seed, "meaning": "a separate fictional sense for testing identity"}
        distinct = coach.add_vocabulary(self.data, **alternate, today=date(2026, 1, 3))
        self.assertNotEqual(distinct["id"], again["id"])
        self.assertEqual(len(self.data["vocabulary"]), 2)

    def test_invalid_or_backdated_reviews_preserve_evidence(self):
        before = deepcopy(self.item)
        with self.assertRaises(ValueError):
            self.retrieve(2, "unsupported")
        with self.assertRaises(ValueError):
            coach.review_vocabulary(self.item, "production", "correct", "", date(2026, 1, 2))
        with self.assertRaises(ValueError):
            coach.review_vocabulary(self.item, "production", "correct", "A response", date(2025, 12, 31))
        self.assertEqual(self.item, before)

    def test_old_record_is_read_without_rewriting_or_losing_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "progress.json"
            original = '{"version": 1, "errors": [{"id": "synthetic-error"}]}'
            path.write_text(original)
            migrated = coach.read_queue(path)
            self.assertEqual(migrated["errors"], [{"id": "synthetic-error"}])
            self.assertEqual(migrated["vocabulary"], [])
            self.assertEqual(path.read_text(), original)

    def test_cli_saves_privately_and_keeps_missed_reviews_due(self):
        with tempfile.TemporaryDirectory() as temporary:
            command = [sys.executable, str(ROOT / "tools/coach.py"), "--data-dir", temporary]
            absent = subprocess.run([*command, "vocabulary-due"], text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(absent.stdout), [])
            self.assertFalse((Path(temporary) / "progress.json").exists())
            flags = [flag for key, value in self.seed.items() for flag in ("--" + key, value)]
            added = subprocess.run([*command, "--today", "2026-01-01", "add-vocabulary", *flags],
                                   text=True, capture_output=True, check=True)
            item = json.loads(added.stdout)
            due = subprocess.run([*command, "--today", "2026-01-09", "vocabulary-due"],
                                 text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(due.stdout)[0]["id"], item["id"])
            reviewed = subprocess.run([*command, "--today", "2026-01-09", "review-vocabulary", item["id"],
                                       "--mode", "production", "--outcome", "correct", "--context",
                                       "New theatre context; We allocate funds to costumes."],
                                      text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(reviewed.stdout)["status"], "usable")
            self.assertEqual(json.loads(reviewed.stdout)["next_due"], "2026-01-12")

    def test_recording_new_encounter_does_not_make_same_day_recall_independent(self):
        coach.add_vocabulary(self.data, **self.seed, today=date(2026, 1, 3))
        self.retrieve(3, "production")
        self.assertEqual(self.item["independent_successes"], 0)


if __name__ == "__main__":
    unittest.main()
