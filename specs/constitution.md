# Constitution

Principles every feature in this repository must respect. If a spec conflicts with one of these, the spec is wrong.

1. **Money is exact.** Amounts are integer minor units with an explicit currency. No floats. Rounding is stated in the spec, never left to the language default.
2. **The reseller is never charged twice for one action.** Every state-changing operation is idempotent on a caller-supplied request ID.
3. **Vendor rules are configuration, not code.** Differences between vendors (minimum seats, how decreases are handled) are data on the plan. No `if vendor == ...`.
4. **Every rule has an ID and a test.** A requirement without a test is not done. A test without a requirement is a question for product.
5. **Reject clearly.** A rejected request returns a specific reason code that a support agent can act on. No generic errors.
6. **Deterministic logic.** Business logic takes dates as input and does not read the clock, so any past invoice can be reproduced.
7. **Spec first.** Behaviour changes start with a change to the spec, reviewed like code.
