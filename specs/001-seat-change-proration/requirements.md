# 001 - Mid-cycle seat changes

Status: Approved · Owner: Product

## Problem
Resellers add and remove seats on monthly subscriptions throughout the billing cycle. Today the adjustment is calculated by hand by the billing team, which is slow and produces two kinds of errors: resellers are under-charged for added seats (revenue leakage), or charged twice when a request is retried.

## Goal
A reseller can change the seat count on an active subscription at any point in the cycle and is charged or credited the correct amount, automatically, exactly once.

## Out of scope
- Annual and multi-year terms
- Changing plan or vendor (upgrade/downgrade)
- Tax calculation (applied downstream on the returned amount)
- Payment collection

## Success measures
- Manual billing corrections for seat changes: down to near zero
- Seat-change requests completed without contacting support
- No duplicate charges from retried requests

## User stories
- As a reseller, I want to add seats today and pay only for the days left in the cycle, so I am not charged for time I did not use.
- As a reseller, I want to know up front whether removing seats gives me a credit or takes effect at renewal, so there are no surprises on the invoice.
- As a support agent, I want a specific reason when a change is rejected, so I can resolve it in one contact.

## Definitions
- **Cycle**: the billing period `[cycle_start, cycle_end)`. `cycle_end` is the renewal date and is not part of the cycle.
- **Remaining days**: days from the effective date (inclusive) to `cycle_end` (exclusive).
- **Decrease policy**: per plan, either `CREDIT` or `END_OF_TERM`.

## Requirements (EARS)

**REQ-001 Increase is prorated.**
WHEN a reseller increases seats on an active subscription, the system SHALL charge `unit_price × added_seats × remaining_days ÷ days_in_cycle` and apply the new seat count immediately.

**REQ-002 Rounding.**
The system SHALL round prorated amounts to the nearest minor unit, with halves rounded away from zero.

**REQ-003 Decrease with credit.**
WHEN a reseller decreases seats AND the plan's decrease policy is `CREDIT`, the system SHALL credit `unit_price × removed_seats × remaining_days ÷ days_in_cycle` and apply the new seat count immediately.

**REQ-004 Decrease at end of term.**
WHEN a reseller decreases seats AND the plan's decrease policy is `END_OF_TERM`, the system SHALL keep the current seat count until `cycle_end`, schedule the new seat count for the next cycle, and charge or credit nothing.

**REQ-005 Minimum seats.**
IF the requested seat count is below the plan's minimum, THEN the system SHALL reject the request with reason `BELOW_MINIMUM_SEATS`.

**REQ-006 Maximum seats.**
IF the plan defines a maximum AND the requested seat count exceeds it, THEN the system SHALL reject the request with reason `ABOVE_MAXIMUM_SEATS`.

**REQ-007 Only active subscriptions.**
IF the subscription status is not `ACTIVE`, THEN the system SHALL reject the request with reason `SUBSCRIPTION_NOT_ACTIVE`.

**REQ-008 No-op is rejected.**
IF the requested seat count equals the current seat count, THEN the system SHALL reject the request with reason `NO_CHANGE`.

**REQ-009 Effective date inside the cycle.**
IF the effective date is before `cycle_start` or on or after `cycle_end`, THEN the system SHALL reject the request with reason `OUTSIDE_BILLING_CYCLE`.

**REQ-010 Idempotency.**
WHEN a request is received with a request ID that has already been processed, the system SHALL return the original result and SHALL NOT change the subscription or create a second charge.

**REQ-011 Rejections change nothing.**
WHEN a request is rejected, the system SHALL leave the subscription unchanged and return an amount of zero.

**REQ-012 Currency.**
The system SHALL return amounts in the subscription's currency as integer minor units.

## Worked examples
Plan: 10.00 EUR per seat per month. Cycle: 1 June to 1 July (30 days).

| # | Current | Requested | Effective | Policy | Result |
|---|---|---|---|---|---|
| 1 | 10 | 13 | 16 June (15 days left) | - | Charge 15.00 EUR, seats = 13 |
| 2 | 10 | 11 | 21 June (10 days left) | - | Charge 3.33 EUR, seats = 11 |
| 3 | 10 | 8 | 16 June | CREDIT | Credit 10.00 EUR, seats = 8 |
| 4 | 10 | 8 | 16 June | END_OF_TERM | 0.00 EUR, seats = 10 now, 8 from 1 July |
| 5 | 10 | 2 | any | min 5 | Rejected: BELOW_MINIMUM_SEATS |
| 6 | 10 | 11 | 1 June (30 days left) | - | Charge 10.00 EUR (full cycle) |

## Resolved questions
- *Is the day of the change billed?* Yes. The effective date counts as a remaining day.
- *A change is made twice on the same day with different request IDs?* They are two changes; each is prorated on its own.
- *Decrease below the minimum under END_OF_TERM?* Rejected (REQ-005 applies regardless of policy).

## Open questions
None.
