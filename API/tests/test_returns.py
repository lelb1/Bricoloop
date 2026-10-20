from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient


def test_owner_returns_loan_and_tool_becomes_available(make_app):
    with TestClient(make_app()) as client:
        before = client.get("/api/tools/4").json()
        response = client.patch("/api/loans/1/return", headers={"X-User-Id": "2"})
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "toolId": 4,
            "borrowerId": 1,
            "startDate": "2026-10-10",
            "endDate": "2026-10-15",
            "status": "returned",
        }
        assert client.get("/api/tools/4").json() == {**before, "status": "available"}
        rows = client.get("/api/loans/received", headers={"X-User-Id": "2"}).json()
        assert next(row for row in rows if row["id"] == 1)["status"] == "returned"
        assert client.patch("/api/loans/1/return", headers={"X-User-Id": "2"}).status_code == 409


@pytest.mark.parametrize("user", ["1", "3", "999"])
def test_only_owner_can_return(make_app, user):
    with TestClient(make_app()) as client:
        assert client.patch("/api/loans/1/return", headers={"X-User-Id": user}).status_code == 403
        assert client.get("/api/tools/4").json()["status"] == "lent"
        rows = client.get("/api/loans/received", headers={"X-User-Id": "2"}).json()
        assert next(row for row in rows if row["id"] == 1)["status"] == "accepted"


@pytest.mark.parametrize("loan_id,owner", [(2, "1"), (3, "3")])
def test_cannot_return_pending_or_already_returned(make_app, loan_id, owner):
    with TestClient(make_app()) as client:
        assert (
            client.patch(f"/api/loans/{loan_id}/return", headers={"X-User-Id": owner}).status_code
            == 409
        )


def test_cannot_return_refused_loan(make_app):
    with TestClient(make_app()) as client:
        client.patch("/api/loans/2", headers={"X-User-Id": "1"}, json={"status": "refused"})
        assert client.patch("/api/loans/2/return", headers={"X-User-Id": "1"}).status_code == 409


def test_unknown_loan_and_missing_profile(make_app):
    with TestClient(make_app()) as client:
        assert client.patch("/api/loans/999/return", headers={"X-User-Id": "1"}).status_code == 404
        assert client.patch("/api/loans/1/return").status_code == 400


def test_returned_dates_can_be_borrowed_again(make_app):
    day = (datetime.now(ZoneInfo("Europe/Paris")).date() + timedelta(days=3)).isoformat()
    with TestClient(make_app()) as client:
        request = client.post(
            "/api/tools/1/loans",
            headers={"X-User-Id": "2"},
            json={"startDate": day, "endDate": day},
        ).json()
        assert (
            client.patch(
                f"/api/loans/{request['id']}",
                headers={"X-User-Id": "1"},
                json={"status": "accepted"},
            ).status_code
            == 200
        )
        assert (
            client.patch(
                f"/api/loans/{request['id']}/return", headers={"X-User-Id": "1"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/tools/1/loans",
                headers={"X-User-Id": "3"},
                json={"startDate": day, "endDate": day},
            ).status_code
            == 201
        )
