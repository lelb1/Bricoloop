from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient


def dates(offset=0):
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    return {
        "startDate": (today + timedelta(days=offset)).isoformat(),
        "endDate": (today + timedelta(days=offset + 2)).isoformat(),
    }


def test_pending_requests_allow_multiple_borrowers(make_app):
    with TestClient(make_app()) as client:
        before = client.get("/api/tools/1").json()
        first = client.post("/api/tools/1/loans", headers={"X-User-Id": "2"}, json=dates())
        assert first.status_code == 201
        assert first.json() == {
            "id": 4,
            "toolId": 1,
            "borrowerId": 2,
            **dates(),
            "status": "pending",
        }
        second = client.post("/api/tools/1/loans", headers={"X-User-Id": "3"}, json=dates())
        assert second.status_code == 201
        assert second.json()["status"] == "pending"
        assert second.json()["id"] != first.json()["id"]
        assert client.get("/api/tools/1").json() == before


@pytest.mark.parametrize(
    "tool,user,change,field",
    [
        (1, "1", {}, "toolId"),
        (1, "2", {"endDate": "2000-01-01"}, "endDate"),
        (1, "2", {"startDate": "2000-01-01"}, "startDate"),
        (4, "1", {}, "toolId"),
        (8, "1", {}, "toolId"),
        (1, "999", {}, "X-User-Id"),
        (1, "2", {"startDate": "invalid"}, "startDate"),
        (1, "2", {"startDate": "2026-02-30"}, "startDate"),
        (1, "2", {"startDate": None}, "startDate"),
        (1, "2", {"borrowerId": 4}, "borrowerId"),
        (1, "2", {"status": "accepted"}, "status"),
    ],
)
def test_rejected_requests(make_app, tool, user, change, field):
    with TestClient(make_app()) as client:
        response = client.post(
            f"/api/tools/{tool}/loans", headers={"X-User-Id": user}, json={**dates(1), **change}
        )
        assert response.status_code == 400
        assert field in str(response.json())


def test_same_day_loan_is_allowed(make_app):
    payload = dates()
    payload["endDate"] = payload["startDate"]
    with TestClient(make_app()) as client:
        assert (
            client.post("/api/tools/1/loans", headers={"X-User-Id": "2"}, json=payload).status_code
            == 201
        )


def test_unknown_tool(make_app):
    with TestClient(make_app()) as client:
        assert (
            client.post(
                "/api/tools/999/loans", headers={"X-User-Id": "2"}, json=dates()
            ).status_code
            == 404
        )


def test_missing_header_and_dates(make_app):
    with TestClient(make_app()) as client:
        assert client.post("/api/tools/1/loans", json=dates()).status_code == 400
        assert (
            client.post("/api/tools/1/loans", headers={"X-User-Id": "2"}, json={}).status_code
            == 400
        )
