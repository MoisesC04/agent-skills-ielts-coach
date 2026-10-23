---
name: ielts-progress-tracker
description: Maintain an evidence-based IELTS review queue and export private session or weekly summaries. Use to resume progress, record recurring errors, vocabulary, results, and preferences; never commit personal history or imply unavailable memory.
---

# IELTS progress tracker

Use English. Check only the current conversation, explicitly provided summaries, and authorized local progress records. If no previous record is accessible, say progress is unavailable and begin a baseline. Do not invent historical sessions or silently scan unrelated personal files or Drive.

Track each error under a stable ID and skill/pattern, with the exact observed example, corrected example, brief reason, observation count, independent retrieval successes, last review, next due, and status. Call a pattern recurring after separate observations, not merely because one sentence contains several mistakes. Retrieval uses a new context before revealing the correction.

Schedule the initial retrieval for the next day. After the first, second, and third independent delayed successes, schedule retrieval in 3, 7, and 14 days respectively. Same-day retries or prompted corrections are assisted evidence and do not advance mastery. An error resets the success sequence and schedules the next day. After four delayed successes mark stabilized, retain the evidence, and spot-check after 30 days. Use the learner's local date if known; otherwise record "next session" rather than guessing a date.

Track vocabulary with meaning, collocation, source/topic, learner sentence, and a later contextual retrieval. Track preferences with provenance (learner-stated or tentative inference) and revise them when corrected.

Separate tutor-verified raw marks with key/source and item IDs, learner-reported results, and inferred Writing/Speaking judgments. Record modality, timing, replays, assistance, confidence, and missing evidence. Never convert a partial set to a band. Pronunciation and a complete Speaking band remain unassessed from transcripts alone.

End each session with an exportable summary containing completed/pending activities, error queue, vocabulary, preferences, next due reviews, next Reading/Writing focus, and one next action. Use `templates/session-log.md` and `templates/weekly-report.md` if present. Displaying a summary is not saving it. State a storage location only after a successful authorized write.

Keep real learner records in ignored `private/` or an explicitly chosen private destination, never GitHub commits or test fixtures. The optional `tools/coach.py` helper stores an error queue only; it does not replace the full summary. Do not access or modify Drive without separate authorization. Repository examples must be synthetic and contain no real learner history or credentials.
