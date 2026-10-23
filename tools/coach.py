"""Dependency-free objective marking and private error/vocabulary review queues.

This helper never estimates IELTS bands and never calls a network service.
"""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
SUCCESS_INTERVALS = (3, 7, 14)


def normalized(text):
    return " ".join(text.strip().casefold().split())


def score(key, responses):
    """Mark an entire identified local set; missing responses count as incorrect."""
    if not isinstance(responses, dict) or not all(isinstance(v, str) for v in responses.values()):
        raise ValueError("Responses must map item IDs to answer strings.")
    if not key.get("source") or not key.get("task_id") or not key.get("items"):
        raise ValueError("An identified source, task ID, and nonempty verified key are required.")
    items = key["items"]
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("Key item IDs must be unique.")
    if set(responses) - {item["id"] for item in items}:
        raise ValueError("Response contains item IDs absent from the key.")
    details = []
    for item in items:
        accepted = item.get("accepted")
        if not accepted or not all(isinstance(a, str) and a.strip() for a in accepted):
            raise ValueError("Each key item needs explicit accepted answers.")
        limit = item.get("max_words")
        if limit is not None and (type(limit) is not int or limit < 1):
            raise ValueError("Word limits must be positive integers.")
        answer = responses.get(item["id"], "")
        within_limit = limit is None or len(answer.split()) <= limit
        correct = within_limit and normalized(answer) in {normalized(a) for a in accepted}
        details.append({"id": item["id"], "correct": correct, "within_word_limit": within_limit})
    return {"task_id": key["task_id"], "source": key["source"], "result_type": "local_raw_score",
            "correct": sum(item["correct"] for item in details), "total": len(items),
            "items": details, "band": None,
            "limitation": "Key-based practice result only; no IELTS band or CEFR inference."}


def read_queue(path):
    if not path.exists():
        return {"version": 1, "errors": [], "vocabulary": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("errors"), list):
        raise ValueError("Unsupported progress record; preserve it and inspect manually.")
    # Older version-1 error queues remain readable; reading never rewrites them.
    if not isinstance(data.setdefault("vocabulary", []), list):
        raise ValueError("Vocabulary must be a list; preserve the record and inspect manually.")
    return data


def save_queue(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def add_error(data, skill, pattern, original, correction, today):
    if not all(value.strip() for value in (pattern, original, correction)):
        raise ValueError("Pattern, observed example, and correction cannot be blank.")
    existing = next((e for e in data["errors"] if e["skill"] == skill
                     and normalized(e["pattern"]) == normalized(pattern)), None)
    if existing and today < date.fromisoformat(existing["last_seen"]):
        raise ValueError("Observation date cannot precede the last observation.")
    if existing is None:
        existing = {"id": uuid.uuid4().hex[:12], "skill": skill, "pattern": pattern,
                    "seen_count": 0, "events": [], "last_review": None}
        data["errors"].append(existing)
    existing.update(original=original, correction=correction, last_seen=today.isoformat(),
                    seen_count=existing["seen_count"] + 1, independent_successes=0,
                    next_due=(today + timedelta(days=1)).isoformat())
    existing["status"] = "recurring" if existing["seen_count"] > 1 else "active"
    existing["events"].append({"date": today.isoformat(), "type": "observation",
                               "original": original, "correction": correction})
    return existing


def review(error, outcome, context, today, independent_allowed=True):
    if not context.strip():
        raise ValueError("Provide the new retrieval context and response evidence.")
    latest = error.get("last_review") or error["last_seen"]
    if today < date.fromisoformat(max(latest, error["last_seen"])):
        raise ValueError("Review date cannot precede recorded evidence.")
    if outcome not in ("correct", "incorrect", "assisted"):
        raise ValueError("Outcome must be correct, incorrect, or assisted.")
    independent = (outcome == "correct" and today >= date.fromisoformat(error["next_due"])
                   and error.get("last_review") != today.isoformat() and independent_allowed)
    error["events"].append({"date": today.isoformat(), "type": "retrieval",
                            "outcome": outcome, "context": context, "independent": independent})
    error["last_review"] = today.isoformat()
    if outcome == "incorrect":
        error.update(independent_successes=0, status="recurring",
                     next_due=(today + timedelta(days=1)).isoformat())
    elif independent:
        successes = error["independent_successes"] + 1
        interval = SUCCESS_INTERVALS[successes - 1] if successes <= len(SUCCESS_INTERVALS) else 30
        error.update(independent_successes=successes,
                     status="stabilized" if successes >= 4 else "stabilizing",
                     next_due=(today + timedelta(days=interval)).isoformat())
    return error


def add_vocabulary(data, expression, meaning, collocation, source, example, today):
    fields = (expression, meaning, collocation, source)
    if not all(value.strip() for value in fields):
        raise ValueError("Expression, meaning, collocation, and source/context are required.")
    entries = data.setdefault("vocabulary", [])
    item = next((entry for entry in entries
                 if normalized(entry["expression"]) == normalized(expression)
                 and normalized(entry["meaning"]) == normalized(meaning)), None)
    if item and today < date.fromisoformat(max(item["last_seen"], item.get("last_review") or item["last_seen"])):
        raise ValueError("Encounter date cannot precede recorded vocabulary evidence.")
    if item is None:
        item = {"id": "v-" + uuid.uuid4().hex[:12], "expression": expression,
                "meaning": meaning, "seen_count": 0, "events": [],
                "last_review": None, "independent_successes": 0,
                "successes_by_mode": {"recognition": 0, "production": 0},
                "status": "learning", "next_due": (today + timedelta(days=1)).isoformat()}
        entries.append(item)
    item.update(collocation=collocation, source=source, last_seen=today.isoformat(),
                seen_count=item["seen_count"] + 1)
    if example.strip():
        item["learner_example"] = example
    item["events"].append({"type": "encounter", "date": today.isoformat(),
                           "source": source, "example": example})
    return item


def review_vocabulary(item, mode, outcome, context, today):
    """Record a supplied judgment; this function does not assess language itself."""
    if mode not in ("recognition", "production"):
        raise ValueError("Vocabulary mode must be recognition or production.")
    duplicate = any(event.get("independent") and
                    normalized(event.get("context", "")) == normalized(context)
                    for event in item["events"])
    same_day_exposure = today <= date.fromisoformat(item["last_seen"])
    review(item, outcome, context, today, independent_allowed=not duplicate and not same_day_exposure)
    event = item["events"][-1]
    event["mode"] = mode
    if duplicate:
        event["limitation"] = "Repeated response/context; no new independent retrieval evidence."
    elif same_day_exposure:
        event["limitation"] = "Same-day encounter; no delayed retrieval evidence."
    if outcome == "incorrect":
        item["successes_by_mode"] = {"recognition": 0, "production": 0}
    elif event["independent"]:
        item["successes_by_mode"][mode] += 1
    production = item["successes_by_mode"]["production"]
    if item["independent_successes"] >= 4 and production >= 2:
        item["status"] = "retained"
    elif production:
        item["status"] = "usable"
    elif item["independent_successes"]:
        item["status"] = "recognized"
    else:
        item["status"] = "learning"
    # Recognition alone must not stretch reviews to the retained-item interval.
    if event["independent"] and item["status"] != "retained":
        item["next_due"] = min(item["next_due"], (today + timedelta(days=14)).isoformat())
    return item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "private")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    commands = parser.add_subparsers(dest="command", required=True)
    grade = commands.add_parser("score", help="Mark an identified key against numbered responses")
    grade.add_argument("key", type=Path)
    grade.add_argument("responses", type=Path)
    commands.add_parser("due", help="Read due errors without writing a file")
    commands.add_parser("vocabulary-due", help="Read due vocabulary without writing a file")
    add = commands.add_parser("add-error")
    add.add_argument("--skill", choices=("listening", "speaking", "reading", "writing"), required=True)
    for field in ("pattern", "original", "correction"):
        add.add_argument("--" + field, required=True)
    retrieve = commands.add_parser("review")
    retrieve.add_argument("id")
    retrieve.add_argument("--outcome", choices=("correct", "incorrect", "assisted"), required=True)
    retrieve.add_argument("--context", required=True, help="New context plus response evidence; use correct only for an independent attempt")
    vocabulary = commands.add_parser("add-vocabulary", help="Record a word or expression in its specific sense")
    for field in ("expression", "meaning", "collocation", "source"):
        vocabulary.add_argument("--" + field, required=True)
    vocabulary.add_argument("--example", default="", help="Learner's example, if available")
    vocab_review = commands.add_parser("review-vocabulary")
    vocab_review.add_argument("id")
    vocab_review.add_argument("--mode", choices=("recognition", "production"), required=True)
    vocab_review.add_argument("--outcome", choices=("correct", "incorrect", "assisted"), required=True)
    vocab_review.add_argument("--context", required=True, help="New retrieval prompt/context and actual learner response")
    args = parser.parse_args()
    if args.command == "score":
        result = score(json.loads(args.key.read_text(encoding="utf-8")),
                       json.loads(args.responses.read_text(encoding="utf-8")))
    else:
        path = args.data_dir / "progress.json"
        # Restrict in-repository writes to the designated private directory.
        # Outside-repository storage is chosen explicitly with --data-dir.
        if args.command not in ("due", "vocabulary-due") and path.resolve().is_relative_to(ROOT):
            if not path.resolve().is_relative_to(ROOT / "private"):
                raise ValueError("Inside this repository, personal records must stay under private/.")
        data = read_queue(path)
        if args.command in ("due", "vocabulary-due"):
            collection = "errors" if args.command == "due" else "vocabulary"
            result = sorted((e for e in data[collection] if date.fromisoformat(e["next_due"]) <= args.today),
                            key=lambda e: e["next_due"])
        elif args.command == "add-error":
            result = add_error(data, args.skill, args.pattern, args.original, args.correction, args.today)
            save_queue(path, data)
        elif args.command == "add-vocabulary":
            result = add_vocabulary(data, args.expression, args.meaning, args.collocation,
                                    args.source, args.example, args.today)
            save_queue(path, data)
        elif args.command == "review-vocabulary":
            item = next((e for e in data["vocabulary"] if e["id"] == args.id), None)
            if item is None:
                raise ValueError("Unknown vocabulary ID; run vocabulary-due or inspect your private queue.")
            result = review_vocabulary(item, args.mode, args.outcome, args.context, args.today)
            save_queue(path, data)
        else:
            error = next((e for e in data["errors"] if e["id"] == args.id), None)
            if error is None:
                raise ValueError("Unknown error ID; run due or inspect your private queue.")
            result = review(error, args.outcome, args.context, args.today)
            save_queue(path, data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Cannot complete request: {error}", file=sys.stderr)
        sys.exit(1)
