from datetime import date

import pytest

from helpers import make_req, make_sub
from seatchange import (DecreasePolicy, RejectReason, SeatChangeRequest, Status,
                        evaluate_seat_change)
from seatchange.proration import round_half_away_from_zero


# --- REQ-002 rounding ---------------------------------------------------------
@pytest.mark.parametrize("num, den, expected", [
    (10, 4, 3),     # 2.5  -> 3
    (-10, 4, -3),   # -2.5 -> -3
    (9, 4, 2),      # 2.25 -> 2
    (11, 4, 3),     # 2.75 -> 3
    (0, 7, 0),
])
def test_req_002_rounds_half_away_from_zero(num, den, expected):
    assert round_half_away_from_zero(num, den) == expected


# --- REQ-001 increase (worked examples 1, 2, 6) --------------------------------
def test_req_001_increase_is_prorated_example_1():
    result = evaluate_seat_change(make_sub(seats=10), make_req(13, day=16))
    assert result.accepted and result.amount_minor == 1500 and result.seats_now == 13


def test_req_001_req_002_increase_rounds_example_2():
    # 1000 * 1 * 10 / 30 = 333.33 -> 333
    result = evaluate_seat_change(make_sub(seats=10), make_req(11, day=21))
    assert result.amount_minor == 333


def test_req_001_increase_on_first_day_charges_full_cycle_example_6():
    result = evaluate_seat_change(make_sub(seats=10), make_req(11, day=1))
    assert result.amount_minor == 1000


def test_req_001_last_day_of_cycle_charges_one_day():
    result = evaluate_seat_change(make_sub(seats=10), make_req(11, day=30))
    assert result.amount_minor == 33     # 1000 / 30 = 33.33


# --- REQ-003 decrease with credit (worked example 3) ---------------------------
def test_req_003_decrease_with_credit_policy_example_3():
    result = evaluate_seat_change(make_sub(seats=10), make_req(8, day=16))
    assert result.accepted and result.amount_minor == -1000 and result.seats_now == 8


# --- REQ-004 decrease at end of term (worked example 4) ------------------------
def test_req_004_decrease_end_of_term_is_scheduled_example_4():
    sub = make_sub(seats=10, policy=DecreasePolicy.END_OF_TERM)
    result = evaluate_seat_change(sub, make_req(8, day=16))
    assert result.accepted
    assert result.amount_minor == 0
    assert result.seats_now == 10 and result.seats_next_cycle == 8


def test_req_004_increase_ignores_end_of_term_policy():
    sub = make_sub(seats=10, policy=DecreasePolicy.END_OF_TERM)
    result = evaluate_seat_change(sub, make_req(13, day=16))
    assert result.amount_minor == 1500 and result.seats_now == 13


# --- Validation: REQ-005..009, REQ-011 -----------------------------------------
def assert_rejected(result, reason, seats=10):
    assert not result.accepted
    assert result.reason is reason
    assert result.amount_minor == 0 and result.seats_now == seats   # REQ-011


def test_req_005_below_minimum_is_rejected_example_5():
    result = evaluate_seat_change(make_sub(min_seats=5), make_req(2))
    assert_rejected(result, RejectReason.BELOW_MINIMUM_SEATS)


def test_req_005_minimum_applies_under_end_of_term_policy():
    sub = make_sub(min_seats=5, policy=DecreasePolicy.END_OF_TERM)
    assert_rejected(evaluate_seat_change(sub, make_req(2)), RejectReason.BELOW_MINIMUM_SEATS)


def test_req_006_above_maximum_is_rejected():
    result = evaluate_seat_change(make_sub(max_seats=20), make_req(21))
    assert_rejected(result, RejectReason.ABOVE_MAXIMUM_SEATS)


def test_req_006_exactly_maximum_is_accepted():
    assert evaluate_seat_change(make_sub(max_seats=20), make_req(20)).accepted


@pytest.mark.parametrize("status", [Status.SUSPENDED, Status.CANCELLED])
def test_req_007_inactive_subscription_is_rejected(status):
    result = evaluate_seat_change(make_sub(status=status), make_req(12))
    assert_rejected(result, RejectReason.SUBSCRIPTION_NOT_ACTIVE)


def test_req_008_no_change_is_rejected():
    assert_rejected(evaluate_seat_change(make_sub(seats=10), make_req(10)), RejectReason.NO_CHANGE)


@pytest.mark.parametrize("effective", [date(2026, 5, 31), date(2026, 7, 1)])
def test_req_009_effective_date_outside_cycle_is_rejected(effective):
    req = SeatChangeRequest("req-1", "sub-1", 12, effective)
    assert_rejected(evaluate_seat_change(make_sub(), req), RejectReason.OUTSIDE_BILLING_CYCLE)


def test_req_007_status_is_checked_before_other_rules():
    """Validation order from design.md: status wins over NO_CHANGE."""
    result = evaluate_seat_change(make_sub(status=Status.SUSPENDED), make_req(10))
    assert result.reason is RejectReason.SUBSCRIPTION_NOT_ACTIVE


# --- REQ-012 currency -----------------------------------------------------------
def test_req_012_amount_is_integer_minor_units_in_subscription_currency():
    result = evaluate_seat_change(make_sub(), make_req(11, day=21))
    assert isinstance(result.amount_minor, int) and result.currency == "EUR"
