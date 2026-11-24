from helpers import make_req, make_sub
from seatchange import DecreasePolicy, SeatChangeService


def service(**kw):
    sub = make_sub(**kw)
    return SeatChangeService({sub.id: sub})


def test_req_001_accepted_increase_updates_stored_seats():
    svc = service()
    svc.change_seats(make_req(13))
    assert svc.get("sub-1").seats == 13


def test_req_004_end_of_term_decrease_is_stored_as_scheduled():
    svc = service(policy=DecreasePolicy.END_OF_TERM)
    svc.change_seats(make_req(8))
    sub = svc.get("sub-1")
    assert sub.seats == 10 and sub.scheduled_seats == 8


def test_req_010_replayed_request_returns_same_result_and_changes_nothing():
    svc = service()
    first = svc.change_seats(make_req(13, request_id="req-A"))
    replay = svc.change_seats(make_req(13, request_id="req-A"))
    assert replay == first
    assert svc.get("sub-1").seats == 13       # not 16


def test_req_010_new_request_id_is_a_new_change():
    svc = service()
    svc.change_seats(make_req(13, request_id="req-A"))
    second = svc.change_seats(make_req(15, request_id="req-B"))
    assert second.amount_minor == 1000 and svc.get("sub-1").seats == 15


def test_req_011_rejected_request_leaves_subscription_unchanged():
    svc = service(min_seats=5)
    before = svc.get("sub-1")
    result = svc.change_seats(make_req(2))
    assert not result.accepted and svc.get("sub-1") == before
