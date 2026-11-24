# 001 - Design

Implements `requirements.md`. Reviewed with engineering.

## Shape
Two layers:
1. **`proration.py`** - a pure function that decides the outcome of one seat-change request. No state, no I/O.
2. **`service.py`** - applies the outcome to the stored subscription and guarantees idempotency.

## Data model
```
Plan            unit_price_minor:int, currency:str, min_seats:int,
                max_seats:int|None, decrease_policy: CREDIT|END_OF_TERM
Subscription    id, plan, seats:int, status: ACTIVE|SUSPENDED|CANCELLED,
                cycle_start:date, cycle_end:date, scheduled_seats:int|None
SeatChangeRequest   request_id:str, subscription_id:str,
                    requested_seats:int, effective_date:date
SeatChangeResult    accepted:bool, reason:RejectReason|None,
                    amount_minor:int   (positive = charge, negative = credit)
                    currency:str, seats_now:int, seats_next_cycle:int|None
```

## Public interface
```python
evaluate_seat_change(subscription, request) -> SeatChangeResult      # pure
SeatChangeService.change_seats(request) -> SeatChangeResult          # stateful, idempotent
```

## Calculation
```
remaining = (cycle_end - effective_date).days
total     = (cycle_end - cycle_start).days
amount    = round_half_away_from_zero(unit_price_minor * delta * remaining / total)
```
All integer arithmetic: `(2 * numerator + denominator) // (2 * denominator)` on the absolute value, sign applied afterwards. (REQ-002, REQ-012)

## Validation order
First failing check wins, so the reason code is predictable (Constitution 5):
1. status is ACTIVE (REQ-007)
2. effective date inside cycle (REQ-009)
3. requested != current (REQ-008)
4. requested >= min (REQ-005)
5. requested <= max (REQ-006)

## Decisions

| Decision | Chosen | Rejected alternative | Why |
|---|---|---|---|
| Proration basis | Daily | Hourly / per second | Matches how vendors invoice; reproducible without time zones |
| Rounding | Once, on the total for the change | Per seat, then sum | Per-seat rounding drifts by up to half a cent per seat |
| Decrease behaviour | Policy on the plan | Branch on vendor | Constitution 3; a new vendor is configuration |
| Idempotency | Store result by `request_id` | Detect duplicates by content | Two identical changes on one day are legitimate |
| Money type | `int` minor units | `Decimal` | Simpler, no context/precision settings to get wrong |

## Not covered here
Persistence (the service uses an in-memory store behind a small interface), invoicing, tax.

## Requirement coverage
| Requirement | Where |
|---|---|
| REQ-001, 002, 003, 004, 012 | `proration.py` calculation |
| REQ-005 to 009, 011 | `proration.py` validation |
| REQ-010, 011 | `service.py` |
