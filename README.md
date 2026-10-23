# IELTS Academic Coach

An English-only, adaptive tutor for IELTS Academic and longer-term progress toward CEFR C1. Start with a 40-minute lesson today, then refine the plan using evidence from actual practice. Twelve weeks is a planning horizon, not a promise of a band score or C1 certification.

## Start today

In Codex, open this repository as a local project and send:

> Use AGENTS.md and agents/ielts-coach.md to start my 40-minute IELTS Academic session. Check any progress summary I provide; otherwise start the baseline. Give me one prompt at a time. Use English throughout.

No package installation, API key, paid service, or third-party library is required. The language model in your current chat delivers the lesson; this repository supplies its instructions and materials. Audio playback uses an external official IELTS player in your browser.

For a busy day, say **“Start my 20-minute session.”** To resume, attach or paste your last private session summary. Without an accessible summary, the tutor will say that previous progress is unavailable instead of inventing it.

## Use in a ChatGPT Project

1. Create a private Project. Copy `prompts/project-instructions.md` into its project instructions.
2. Upload `agents/ielts-coach.md`, `config/learning-plan.yaml`, `prompts/first-session.md`, `exercises/baseline.md`, `references/sources.md`, `references/assessment.md`, and `templates/session-log.md`. Add the six `SKILL.md` files when needed; rename uploaded copies by skill if duplicate filenames are confusing.
3. Send the start prompt above. Keep your private summaries in that private project or export them outside GitHub. Upload the latest summary in a new chat when continuity is uncertain.

GitHub by itself does **not** deploy an agent, run lessons, synchronize Project files, or install skills into ChatGPT. Uploaded Project copies must be refreshed after repository changes. A normal Project uses these files as context and instructions; it does not gain tools or native skill execution just because a file is named `SKILL.md`.

Codex discovers repository skills in `.agents/skills/`. `AGENTS.md` contains workspace guidance; it is not an executable agent. The `agents/` folder contains a tutor specification, not an agent server. Current operating guidance: [ChatGPT Projects](https://help.openai.com/en/articles/10169521-projects-in-chatgpt) and [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills), checked 2026-10-23.

## What a lesson does

| Routine | Check-in and retrieval | Listening | Speaking | Reading or Writing | Review and export |
| --- | ---: | ---: | ---: | ---: | ---: |
| Standard | 3 min | 10 min | 10 min | 12 min | 5 min |
| Busy day | 2 min | 5 min | 5 min | 5 min | 3 min |

Listening and Speaking happen every study day. Reading and Writing alternate by completed session, with both sampled in the first baseline. Short exercises are training, not full tests. Full timed sections require a separate extended appointment. Use a learner timer; the tutor must not pretend to measure elapsed time without a clock.

The tutor retrieves due errors, gives feedback at natural pauses, requests a correction attempt, and revisits it later. It tracks evidence, corrected examples, vocabulary in context, confidence, preferences, and the next activity. Partial reading/listening results are raw fractions, never invented IELTS bands. Speaking and Writing estimates remain provisional and need suitable evidence. Pronunciation requires genuine accessible speech audio.

## Materials and files

- `agents/ielts-coach.md`: session flow and adaptive decisions.
- `.agents/skills/`: Listening, Speaking, Reading, Writing, learning planner, and progress tracker.
- `config/learning-plan.yaml`: editable defaults, weekly milestones, and adaptation rules.
- `prompts/first-session.md` and `exercises/baseline.md`: usable diagnostic and original practice tasks.
- `references/sources.md` and `references/assessment.md`: official links, criteria, and assessment limits.
- `templates/`: exportable session summary and weekly report.
- `tools/coach.py`: optional Python 3.10+ helper for objective marking and spaced error review. It is not a tutor or an AI scorer.
- `tests/`: synthetic fixtures, deterministic checks, and manual behavior scenarios.

## Optional local helper

```text
python tools/coach.py score tests/fixtures/reading-key.json tests/fixtures/reading-response.json
python tools/coach.py due
python tools/coach.py add-error --skill writing --pattern "Subject-verb agreement" --original "The chart show growth." --correction "The chart shows growth."
python tools/coach.py review ERROR_ID --outcome correct --context "A new sentence written without a hint."
python -m unittest discover -s tests -v
python tools/validate_repository.py
```

Replace `ERROR_ID` with the ID returned by `add-error`. The example sentences above are fictional. The helper saves only when explicitly called to add or review an error. Data goes to ignored `private/progress.json`; `due` is read-only. For a separate directory use `python tools/coach.py --data-dir PATH due`. Use the learner's local date, or supply `--today YYYY-MM-DD` before the command. Export the session template for the richer lesson record; the helper stores an error queue only.

## Privacy and maintenance

Commit tutor specifications and synthetic examples only. Never commit real learner answers, session logs, recordings, contact information, credentials, or progress history, even to this private repository. Use `private/` locally for personal records; it is ignored. Before committing, review every staged file. Ignore rules do not protect files already tracked or files deliberately forced into Git.

Google Drive has no role in this MVP. No Drive files are created or modified. A future private store may hold exported summaries, after explicit setup. The tutor must never claim persistence beyond tools and files it actually accessed.

After a real session, refine one demonstrated issue at a time. Add a synthetic regression scenario, update the relevant instruction, and rerun validation. Do not copy the learner's private history into test fixtures. Recheck official links if a player or criterion changes. No full copyrighted tests, transcripts, or audio are redistributed here; official materials stay on their providers' sites. This project is independent of the IELTS partners.
An adaptive, English-only IELTS Academic tutor with evidence-based feedback and private progress tracking.
