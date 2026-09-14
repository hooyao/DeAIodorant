# Contributing to DeAIodorant

DeAIodorant is currently building its research foundation. Contributions should
strengthen reproducibility and reader-focused Chinese text refinement without
overstating what the available corpus can establish.

## Before starting

Read `AGENTS.md`, the relevant protocol in `docs/`, and the tests around the code
you plan to change. Current work belongs on the `init` branch; do not update
`main` until the maintainer explicitly changes the branch policy.

For corpus or evaluation work, state:

- the research question;
- source and date coverage;
- inclusion, exclusion, and deduplication rules;
- visibility and quality signals;
- known confounders and missing data;
- the exact command that reproduces generated artifacts.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## Changes

- Keep pull requests focused on one research, product, or infrastructure goal.
- Add or update tests for behavior changes.
- Keep default tests offline and deterministic.
- Do not modify frozen gold data after inspecting final-test outcomes.
- Do not commit credentials, cookies, personal data, model weights, or scraped
  content without provenance and a documented reason it may be redistributed.
- Preserve existing command-line entry points unless a breaking change is
  intentional and documented.
- Use English for code, comments, identifiers, documentation, and commit
  messages. Chinese is appropriate for corpus fixtures and language examples.

## Commit messages

Use a short imperative or Conventional Commit-style subject, for example:

```text
feat: add matched-cohort sampler
fix: preserve negation during sentence fusion
docs: record translation benchmark protocol
```

## Pull request checklist

- [ ] The change has a clear scope and no unrelated data rewrites.
- [ ] Tests pass locally.
- [ ] Generated artifacts include reproduction metadata.
- [ ] Corpus changes preserve monthly metadata invariants.
- [ ] Refinement changes preserve meaning and expose an inspectable diff.
- [ ] Documentation reflects any changed behavior or project boundary.
