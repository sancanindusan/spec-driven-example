from datetime import date

from seatchange import (DecreasePolicy, Plan, SeatChangeRequest, Status,
                        Subscription)

JUNE_1, JULY_1 = date(2026, 6, 1), date(2026, 7, 1)   # 30-day cycle


def make_sub(seats=10, status=Status.ACTIVE, policy=DecreasePolicy.CREDIT,
             min_seats=1, max_seats=None, price=1000):
    plan = Plan(unit_price_minor=price, currency="EUR", min_seats=min_seats,
                max_seats=max_seats, decrease_policy=policy)
    return Subscription(id="sub-1", plan=plan, seats=seats, status=status,
                        cycle_start=JUNE_1, cycle_end=JULY_1)


def make_req(seats, day=16, request_id="req-1"):
    return SeatChangeRequest(request_id=request_id, subscription_id="sub-1",
                             requested_seats=seats, effective_date=date(2026, 6, day))
