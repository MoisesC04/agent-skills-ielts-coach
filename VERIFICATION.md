# MVP verification

Verified on 2026-10-23 before the first tutor-specification commit.

- Authenticated owner: `MoisesC04`; remote visibility independently confirmed as private through the connected GitHub service.
- Six skill manifests passed the bundled skill-creator validator (required YAML name and description, naming, and scaffold checks).
- Learning plan parsed as YAML; twelve weeks present; standard/baseline routines total 40 minutes and the busy routine totals 20.
- Ten deterministic helper regression tests passed: raw marking, word limits, missing answers, spelling, invalid keys, spaced retrieval, relapse, repeated patterns, and storage behavior.
- Repository validator passed: skill packaging, local Markdown links, and exclusions for private progress, recordings, and secrets files.
- Original reading fixture produced 3/4 and no band estimate. Reading an absent review queue returned an empty list without creating personal records.
- Official IELTS format pages, scoring page, descriptors, and sample index/key were retrieved. The note-completion player opened items 1–7 and displayed Audio is Playing after Play was selected. Learner-side audibility and the model's acoustic access still need checking in each session.

The manual model-behavior scenarios in `tests/behavioral-scenarios.md` are supplied for iterative acceptance testing; they have not been independently executed as a model evaluation. Automated checks cannot prove teaching quality, scoring judgment, user playback, pronunciation accuracy, persistent memory, or progress toward a target score. No real learner diagnostic or assessment has yet been performed by this repository.

The tutor is ready for instruction-driven use in the current chat or a configured Project/Codex workspace. It is not an autonomous hosted service. Python is optional for local queue/marking utilities; those utilities use only the standard library. No new third-party runtime packages are required.

## Vocabulary review update — 2026-10-23

The repository is now public. Learner records remain outside version control. Vocabulary tracking includes explicit recognition/production evidence, due dates, and learning/recognized/usable/retained states. Retention requires delayed independent production; copied, hinted, and same-day answers do not advance it.

- All 18 automated tests passed, including eight vocabulary cases covering recognition-only limits, delayed production, relapse, repeated contexts, distinct senses, backward-compatible reads, and a full local command-line save/review cycle with synthetic data.
- Repository validation and the updated progress-tracker skill manifest validation passed.
- Four synthetic tutoring scenarios were manually answered and self-reviewed in the implementation session: due vocabulary before new items, recognition without production, copied examples, and resuming after missed days. This walkthrough is not an independent model evaluation; the broader scenario suite remains available for real-session testing.
- Existing lesson time budgets remain unchanged. No real learner vocabulary, study records, or Drive data were created or published in this update.
