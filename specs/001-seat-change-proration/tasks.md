# 001 - Tasks

Work top to bottom. Each task is done when its tests pass. One task per commit.

- [x] **T1 Domain model** - dataclasses and enums from `design.md`. *(REQ-012)*
- [x] **T2 Rounding helper** - integer half-away-from-zero division, with tests for .5 boundaries and negatives. *(REQ-002)*
- [x] **T3 Validation** - checks in the order given in `design.md`; each returns its reason code and a zero amount. *(REQ-005, 006, 007, 008, 009, 011)*
- [x] **T4 Increase** - prorated charge, seats applied immediately. Cover worked examples 1, 2, 6. *(REQ-001)*
- [x] **T5 Decrease, CREDIT** - prorated credit as a negative amount. Worked example 3. *(REQ-003)*
- [x] **T6 Decrease, END_OF_TERM** - no amount, seats scheduled for next cycle. Worked example 4. *(REQ-004)*
- [x] **T7 Service + idempotency** - apply accepted results to the store; replay returns the stored result and changes nothing. *(REQ-010, 011)*
- [x] **T8 Traceability check** - test that fails if any `REQ-NNN` in `requirements.md` is not referenced in `tests/`. *(Constitution 4)*
