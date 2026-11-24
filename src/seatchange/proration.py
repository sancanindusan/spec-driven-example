"""Pure decision logic for one seat-change request. No state, no I/O."""
from __future__ import annotations

from .models import (DecreasePolicy, RejectReason, SeatChangeRequest,
                     SeatChangeResult, Status, Subscription)


def round_half_away_from_zero(numerator: int, denominator: int) -> int:
    """Integer division rounded to nearest, halves away from zero (REQ-002)."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    return sign * ((2 * abs(numerator) + denominator) // (2 * denominator))


def _reject(sub: Subscription, reason: RejectReason) -> SeatChangeResult:
    # REQ-011: nothing changes, amount is zero.
    return SeatChangeResult(accepted=False, amount_minor=0,
                            currency=sub.plan.currency, seats_now=sub.seats,
                            seats_next_cycle=sub.scheduled_seats, reason=reason)


def _validate(sub: Subscription, req: SeatChangeRequest) -> RejectReason | None:
    """Checks in the order fixed by design.md; first failure wins."""
    plan = sub.plan
    if sub.status is not Status.ACTIVE:                                  # REQ-007
        return RejectReason.SUBSCRIPTION_NOT_ACTIVE
    if not (sub.cycle_start <= req.effective_date < sub.cycle_end):     # REQ-009
        return RejectReason.OUTSIDE_BILLING_CYCLE
    if req.requested_seats == sub.seats:                                # REQ-008
        return RejectReason.NO_CHANGE
    if req.requested_seats < plan.min_seats:                            # REQ-005
        return RejectReason.BELOW_MINIMUM_SEATS
    if plan.max_seats is not None and req.requested_seats > plan.max_seats:  # REQ-006
        return RejectReason.ABOVE_MAXIMUM_SEATS
    return None


def evaluate_seat_change(sub: Subscription, req: SeatChangeRequest) -> SeatChangeResult:
    reason = _validate(sub, req)
    if reason is not None:
        return _reject(sub, reason)

    plan = sub.plan
    delta = req.requested_seats - sub.seats

    # REQ-004: decrease takes effect at renewal, no money moves.
    if delta < 0 and plan.decrease_policy is DecreasePolicy.END_OF_TERM:
        return SeatChangeResult(accepted=True, amount_minor=0, currency=plan.currency,
                                seats_now=sub.seats, seats_next_cycle=req.requested_seats)

    # REQ-001 / REQ-003: prorate on remaining days, round once on the total.
    remaining = (sub.cycle_end - req.effective_date).days
    total = (sub.cycle_end - sub.cycle_start).days
    amount = round_half_away_from_zero(plan.unit_price_minor * delta * remaining, total)
    return SeatChangeResult(accepted=True, amount_minor=amount, currency=plan.currency,
                            seats_now=req.requested_seats,
                            seats_next_cycle=sub.scheduled_seats)
