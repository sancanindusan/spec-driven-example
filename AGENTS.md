# AGENTS.md

Context for coding agents working in this repository.

## Project
Nimbus is a (fictional) B2B marketplace where resellers buy and manage cloud subscriptions from multiple vendors. This repo contains the seat-change service.

## Source of truth
- Each feature has one spec: `specs/NNN-name/spec.md`. Product owns Context, Requirements, Scope and Assumptions; tech design owns Solution.
- If code and spec disagree, the spec wins. Do not "fix" the spec to match the code; stop and ask.
- Do not implement behaviour that has no requirement ID. Propose a spec change instead.

## Commands
- Run tests: `python -m pytest`
- Run one test file: `python -m pytest tests/test_proration.py`

## Rules
- Money is integer minor units (cents). Never use `float` for money.
- Domain logic in `src/seatchange/` is pure: no I/O, no clock access. Dates are passed in.
- Every test references the requirement it verifies (e.g. `REQ-003`) in its name or docstring.
- Work through the Tasks list in the spec in order. Tick a task only when its tests pass.
- Keep changes small: one task per commit.

## Do not
- Add dependencies without asking.
- Change public function signatures listed in the spec's Contract without updating the spec first.
- Guess vendor rules. If a rule is not in the spec, it is an open question.
