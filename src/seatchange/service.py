"""Applies seat changes to stored subscriptions, exactly once per request ID."""
from __future__ import annotations

from dataclasses import replace

from .models import SeatChangeRequest, SeatChangeResult, Subscription
from .proration import evaluate_seat_change


class SeatChangeService:
    def __init__(self, subscriptions: dict[str, Subscription] | None = None):
        self._subscriptions: dict[str, Subscription] = dict(subscriptions or {})
        self._results: dict[str, SeatChangeResult] = {}

    def get(self, subscription_id: str) -> Subscription:
        return self._subscriptions[subscription_id]

    def change_seats(self, req: SeatChangeRequest) -> SeatChangeResult:
        # REQ-010: a replayed request returns the original result, changes nothing.
        if req.request_id in self._results:
            return self._results[req.request_id]

        sub = self._subscriptions[req.subscription_id]
        result = evaluate_seat_change(sub, req)
        if result.accepted:                                   # REQ-011 otherwise
            self._subscriptions[sub.id] = replace(
                sub, seats=result.seats_now, scheduled_seats=result.seats_next_cycle)
        self._results[req.request_id] = result
        return result
