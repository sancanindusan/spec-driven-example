"""Domain model. See specs/001-seat-change-proration/design.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Status(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class DecreasePolicy(Enum):
    CREDIT = "CREDIT"
    END_OF_TERM = "END_OF_TERM"


class RejectReason(Enum):
    SUBSCRIPTION_NOT_ACTIVE = "SUBSCRIPTION_NOT_ACTIVE"
    OUTSIDE_BILLING_CYCLE = "OUTSIDE_BILLING_CYCLE"
    NO_CHANGE = "NO_CHANGE"
    BELOW_MINIMUM_SEATS = "BELOW_MINIMUM_SEATS"
    ABOVE_MAXIMUM_SEATS = "ABOVE_MAXIMUM_SEATS"


@dataclass(frozen=True)
class Plan:
    unit_price_minor: int          # price per seat per cycle, minor units
    currency: str
    min_seats: int = 1
    max_seats: int | None = None
    decrease_policy: DecreasePolicy = DecreasePolicy.CREDIT


@dataclass(frozen=True)
class Subscription:
    id: str
    plan: Plan
    seats: int
    status: Status
    cycle_start: date
    cycle_end: date                # exclusive: the renewal date
    scheduled_seats: int | None = None


@dataclass(frozen=True)
class SeatChangeRequest:
    request_id: str
    subscription_id: str
    requested_seats: int
    effective_date: date


@dataclass(frozen=True)
class SeatChangeResult:
    accepted: bool
    amount_minor: int              # positive = charge, negative = credit
    currency: str
    seats_now: int
    seats_next_cycle: int | None = None
    reason: RejectReason | None = None
