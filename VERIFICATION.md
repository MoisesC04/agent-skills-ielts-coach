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
