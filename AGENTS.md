# agentic-research — Agent Context

An AI-agent pipeline of composable skills for literature and systematic reviews, aligned to
PRISMA 2020, Cochrane review conduct, and GRADE.

## Governing document

`.specify/memory/constitution.md` (v1.0.0) governs this repository and supersedes conflicting
practice elsewhere. The two non-negotiable principles are:

- **II. Keyless, stdlib-only baseline** — no dependency may be introduced, including for tests.
- **V. Humans where LLMs are weak** — risk-of-bias appraisal and numeric verification are
  human-gated; a machine rating is provisional until confirmed.

The other five: standards are enforced not described; skills are self-contained and portable
(no cross-skill imports); fail closed; gates assert only what is mechanically decidable; AI
provenance is recorded.

## Working rules that catch people out

- **Never import across skills.** A skill directory must run when copied out on its own. Pass
  cross-artifact data as a CLI file path instead.
- **Never add a dependency**, including `pytest`. Tests use stdlib `unittest`.
- **Fail closed**: reject unknown keys, reject empty collections, report missing rather than
  defaulting to zero.
- **State what a check cannot verify** whenever you add or change one.

## Current feature

<!-- SPECKIT START -->
Active plan: [specs/001-standards-enforcement-parity/plan.md](specs/001-standards-enforcement-parity/plan.md)
<!-- SPECKIT END -->

## Layout

- `skills/<name>/SKILL.md` — agent instructions; `README.md` — human docs; optional `scripts/`
  and `references/`.
- `steering/ai-research-provenance.md` — provenance stamping and AI-disclosure convention.
- `tests/` — stdlib unittest suite; the only place shared helper code is permitted.
- `specs/` — speckit feature specifications.

## Tests

```bash
python -m unittest discover -s tests -v
```

No installation step. No network access during tests.
