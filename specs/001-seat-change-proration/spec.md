# [SPEC] Mid-cycle seat changes

| Field | Value |
|---|---|
| Status | **APPROVED**<br>Requirements: Approved<br>High-Level Solution: Done<br>Low-Level Solution: Done |
| Authors | PO: requirements, decision table, acceptance criteria<br>Tech design: solution sections |
| Stakeholders | Billing operations, Reseller support |
| References | None (fictional product) |

## Context

### Background and problem statement
Resellers add and remove seats on monthly subscriptions throughout the billing cycle. The adjustment is calculated by hand by the billing team. That is slow, and it produces two kinds of errors: resellers are under-charged for added seats, or charged twice when a request is retried.

Billing operations want a seat change to be charged or credited automatically, correctly, and exactly once.

What exists today:
- **Subscription**: has a plan, a seat count, a status (`ACTIVE`, `SUSPENDED`, `CANCELLED`) and a monthly billing cycle `[cycle_start, cycle_end)`. `cycle_end` is the renewal date and is not part of the cycle.
- **Plan**: price per seat per cycle, currency, minimum seats, optional maximum seats.
- **Seat change**: done by a billing operator, who edits the seat count and adds a manual invoice line.
- **Vendor rules**: some vendors refund removed seats immediately; others keep them billable until renewal. Today this is knowledge in the billing team, not data.

## Requirements

### Functional requirements

| ID | Requirement |
|---|---|
| REQ-001 | When seats are increased on an active subscription, the charge is `unit_price × added_seats × remaining_days ÷ days_in_cycle`, and the new seat count applies immediately. Remaining days run from the effective date (inclusive) to `cycle_end` (exclusive). |
| REQ-002 | Prorated amounts are rounded to the nearest minor unit, halves away from zero. Rounding happens once, on the total for the change. |
| REQ-003 | When seats are decreased and the plan's decrease policy is `CREDIT`, the credit is `unit_price × removed_seats × remaining_days ÷ days_in_cycle`, and the new seat count applies immediately. |
| REQ-004 | When seats are decreased and the plan's decrease policy is `END_OF_TERM`, the current seat count stays until `cycle_end`, the new seat count is scheduled for the next cycle, and nothing is charged or credited. |
| REQ-005 | A requested seat count below the plan's minimum is rejected with reason `BELOW_MINIMUM_SEATS`. This applies under both decrease policies. |
| REQ-006 | If the plan defines a maximum, a requested seat count above it is rejected with reason `ABOVE_MAXIMUM_SEATS`. |
| REQ-007 | If the subscription status is not `ACTIVE`, the request is rejected with reason `SUBSCRIPTION_NOT_ACTIVE`. |
| REQ-008 | A requested seat count equal to the current seat count is rejected with reason `NO_CHANGE`. |
| REQ-009 | An effective date before `cycle_start`, or on or after `cycle_end`, is rejected with reason `OUTSIDE_BILLING_CYCLE`. |
| REQ-010 | A request with a request ID that was already processed returns the original result. It does not change the subscription and does not create a second charge. |
| REQ-011 | A rejected request leaves the subscription unchanged and returns an amount of zero. |
| REQ-012 | Amounts are returned in the subscription's currency as integer minor units. |

### Decision table

| Change | Decrease policy | Validations | Result |
|---|---|---|---|
| Increase | any | pass | Prorated charge. Seats applied now. |
| Decrease | `CREDIT` | pass | Prorated credit. Seats applied now. |
| Decrease | `END_OF_TERM` | pass | No amount. Seats unchanged now, new count from next cycle. |
| any | any | fail | Rejected with the first failing reason. No amount. Nothing changes. |
| any (replayed request ID) | any | any | Original result returned. Nothing changes. |

When more than one validation fails, the reason is the first in this order: status (REQ-007), effective date (REQ-009), no change (REQ-008), minimum (REQ-005), maximum (REQ-006).

### Worked examples
Plan: 10.00 EUR per seat per month. Cycle: 1 June to 1 July (30 days).

| # | Current | Requested | Effective | Policy | Result |
|---|---|---|---|---|---|
| 1 | 10 | 13 | 16 June (15 days left) | any | Charge 15.00 EUR, seats = 13 |
| 2 | 10 | 11 | 21 June (10 days left) | any | Charge 3.33 EUR, seats = 11 |
| 3 | 10 | 8 | 16 June | `CREDIT` | Credit 10.00 EUR, seats = 8 |
| 4 | 10 | 8 | 16 June | `END_OF_TERM` | 0.00 EUR, seats = 10 now, 8 from 1 July |
| 5 | 10 | 2 | any | minimum 5 | Rejected: `BELOW_MINIMUM_SEATS` |
| 6 | 10 | 11 | 1 June (30 days left) | any | Charge 10.00 EUR (full cycle) |

### Edge cases
- Change on the first day of the cycle: the full cycle price is charged (REQ-001).
- Change on the last day of the cycle: one day is charged (REQ-001).
- Two changes on the same day with different request IDs: two separate changes, each prorated on its own (REQ-010).
- Decrease below the minimum under `END_OF_TERM`: rejected, even though nothing would change until renewal (REQ-005).
- Requested seat count exactly at the maximum: accepted (REQ-006).
- Suspended subscription with a no-change request: rejected as `SUBSCRIPTION_NOT_ACTIVE`, not `NO_CHANGE` (validation order).

### Acceptance criteria

**AC-1 Prorated increase (REQ-001, REQ-012)**
GIVEN an active subscription with 10 seats at 10.00 EUR on a 30-day cycle
WHEN seats are changed to 13 with 15 days remaining
THEN the charge is 15.00 EUR
AND the subscription has 13 seats

**AC-2 Rounding (REQ-002)**
GIVEN the same subscription
WHEN seats are changed to 11 with 10 days remaining
THEN the charge is 3.33 EUR

**AC-3 Decrease with credit (REQ-003)**
GIVEN the plan's decrease policy is `CREDIT`
WHEN seats are changed from 10 to 8 with 15 days remaining
THEN the credit is 10.00 EUR
AND the subscription has 8 seats

**AC-4 Decrease at end of term (REQ-004)**
GIVEN the plan's decrease policy is `END_OF_TERM`
WHEN seats are changed from 10 to 8
THEN nothing is charged or credited
AND the subscription has 10 seats now and 8 scheduled for the next cycle

**AC-5 Seat limits (REQ-005, REQ-006, REQ-011)**
GIVEN a plan with a minimum of 5 and a maximum of 20 seats
WHEN seats are changed to 2, or to 21
THEN the request is rejected with `BELOW_MINIMUM_SEATS`, or `ABOVE_MAXIMUM_SEATS`
AND the amount is zero and the subscription is unchanged

**AC-6 Subscription not active (REQ-007, REQ-011)**
GIVEN a subscription that is `SUSPENDED` or `CANCELLED`
WHEN a seat change is requested
THEN the request is rejected with `SUBSCRIPTION_NOT_ACTIVE`

**AC-7 No change (REQ-008)**
GIVEN an active subscription with 10 seats
WHEN seats are changed to 10
THEN the request is rejected with `NO_CHANGE`

**AC-8 Effective date outside the cycle (REQ-009)**
GIVEN a cycle from 1 June to 1 July
WHEN the effective date is 31 May, or 1 July
THEN the request is rejected with `OUTSIDE_BILLING_CYCLE`

**AC-9 Retried request (REQ-010)**
GIVEN a seat change from 10 to 13 was processed with request ID A
WHEN the same request is sent again with request ID A
THEN the original result is returned
AND the subscription still has 13 seats and no second charge exists

### Non-functional requirements
- Money is exact: integer minor units, no floating point.
- The calculation is deterministic: dates are inputs, so any past result can be reproduced.
- Vendor differences are data on the plan, not branches in code.
- Every requirement is covered by at least one automated test that names it.

## Scope

### In scope
- Seat increases and decreases on active monthly subscriptions.
- Proration, rounding, decrease policy, seat limits.
- Rejection reasons and idempotent retries.

### Out of scope
- Annual and multi-year terms.
- Changing plan or vendor.
- Tax (applied downstream on the returned amount).
- Payment collection and invoice generation.
- Persistence: the example keeps state in memory.

## Assumptions
- Every plan has exactly one decrease policy. If a vendor needs a third behaviour (for example, credit only within a grace period), REQ-003 and REQ-004 change.
- Billing cycles are whole days in a single time zone. If cycles can start mid-day, REQ-001 and REQ-009 change.
- The caller always supplies a request ID. If it can be missing, REQ-010 needs a fallback.

## Solution

### High-level solution
*Audience: architects, tech leads, reviewers.*

Two layers:
1. A pure function that decides the outcome of one seat-change request. No state, no I/O, no clock.
2. A service that applies the outcome to the stored subscription and returns the stored result for a replayed request ID.

| Decision | Chosen | Rejected | Why |
|---|---|---|---|
| Proration basis | Daily | Hourly, per second | Matches how vendors invoice; no time-zone ambiguity |
| Rounding | Once, on the total | Per seat, then sum | Per-seat rounding drifts by up to half a cent per seat |
| Decrease behaviour | Policy on the plan | Branch on vendor | A new vendor is configuration |
| Idempotency | Store result by request ID | Detect duplicates by content | Two identical changes on one day are legitimate |
| Money type | `int` minor units | `Decimal` | No precision settings to get wrong |

### Low-level solution
*Audience: engineers and coding agents implementing the feature.*

**Contract**

```
Plan                unit_price_minor:int, currency:str, min_seats:int,
                    max_seats:int|None, decrease_policy: CREDIT|END_OF_TERM
Subscription        id, plan, seats:int, status, cycle_start:date,
                    cycle_end:date, scheduled_seats:int|None
SeatChangeRequest   request_id:str, subscription_id:str,
                    requested_seats:int, effective_date:date
SeatChangeResult    accepted:bool, reason:RejectReason|None,
                    amount_minor:int (positive = charge, negative = credit),
                    currency:str, seats_now:int, seats_next_cycle:int|None
```

```python
evaluate_seat_change(subscription, request) -> SeatChangeResult    # pure
SeatChangeService.change_seats(request) -> SeatChangeResult        # stateful, idempotent
```

**Calculation**

```
remaining = (cycle_end - effective_date).days
total     = (cycle_end - cycle_start).days
amount    = round_half_away_from_zero(unit_price_minor * delta * remaining, total)
```

Integer arithmetic only: `(2 * |numerator| + denominator) // (2 * denominator)`, sign applied afterwards.

**Tasks**

- [x] T1 Domain model *(REQ-012)*
- [x] T2 Rounding helper *(REQ-002)*
- [x] T3 Validation in the order of the decision table *(REQ-005 to REQ-009, REQ-011)*
- [x] T4 Increase *(REQ-001)*
- [x] T5 Decrease with `CREDIT` *(REQ-003)*
- [x] T6 Decrease with `END_OF_TERM` *(REQ-004)*
- [x] T7 Service and idempotency *(REQ-010, REQ-011)*
- [x] T8 Traceability check: fails if a requirement has no test
