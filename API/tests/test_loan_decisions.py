from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient


def new_request(client):
    day = (datetime.now(ZoneInfo("Europe/Paris")).date() + timedelta(days=2)).isoformat()
    response = client.post(
        "/api/tools/1/loans", headers={"X-User-Id": "2"}, json={"startDate": day, "endDate": day}
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.parametrize("decision,tool_status", [("accepted", "lent"), ("refused", "available")])
def test_owner_decision_persists_and_only_pending_can_be_decided(make_app, decision, tool_status):
    with TestClient(make_app()) as client:
        loan_id = new_request(client)
        before = client.get("/api/tools/1").json()
        response = client.patch(
            f"/api/loans/{loan_id}", headers={"X-User-Id": "1"}, json={"status": decision}
        )
        assert response.status_code == 200
        assert response.json()["status"] == decision
        assert client.get("/api/tools/1").json() == {**before, "status": tool_status}
        received = client.get("/api/loans/received", headers={"X-User-Id": "1"}).json()
        loan = next(row for row in received if row["id"] == loan_id)
        assert loan["status"] == decision
        assert loan["toolName"] == "Perceuse Bosch"
        assert loan["borrower"]["firstName"] == "Marc"
        for status in ["accepted", "refused"]:
            assert (
                client.patch(
                    f"/api/loans/{loan_id}", headers={"X-User-Id": "1"}, json={"status": status}
                ).status_code
                == 409
            )
        assert client.get("/api/tools/1").json()["status"] == tool_status


@pytest.mark.parametrize("loan_id", [1, 3])
def test_already_accepted_or_returned_is_409(make_app, loan_id):
    owner = "2" if loan_id == 1 else "3"
    with TestClient(make_app()) as client:
        assert (
            client.patch(
                f"/api/loans/{loan_id}", headers={"X-User-Id": owner}, json={"status": "refused"}
            ).status_code
            == 409
        )


@pytest.mark.parametrize("user", ["2", "3", "999"])
def test_other_users_cannot_decide(make_app, user):
    with TestClient(make_app()) as client:
        before = client.get("/api/tools/1").json()
        response = client.patch(
            "/api/loans/2", headers={"X-User-Id": user}, json={"status": "accepted"}
        )
        assert response.status_code == 403
        assert client.get("/api/tools/1").json() == before
        received = client.get("/api/loans/received", headers={"X-User-Id": "1"}).json()
        assert next(row for row in received if row["id"] == 2)["status"] == "pending"


def test_received_requests_filtered_by_owner(make_app):
    with TestClient(make_app()) as client:
        assert {
            r["id"] for r in client.get("/api/loans/received", headers={"X-User-Id": "1"}).json()
        } == {2}
        assert {
            r["id"] for r in client.get("/api/loans/received", headers={"X-User-Id": "2"}).json()
        } == {1}
        assert client.get("/api/loans/received", headers={"X-User-Id": "4"}).json() == []


@pytest.mark.parametrize(
    "payload",
    [{}, {"status": "pending"}, {"status": "returned"}, {"status": "accepted", "borrowerId": 1}],
)
def test_invalid_decision_is_400(make_app, payload):
    with TestClient(make_app()) as client:
        assert (
            client.patch("/api/loans/2", headers={"X-User-Id": "1"}, json=payload).status_code
            == 400
        )


def test_unknown_request_and_missing_profile(make_app):
    with TestClient(make_app()) as client:
        assert (
            client.patch(
                "/api/loans/999", headers={"X-User-Id": "1"}, json={"status": "accepted"}
            ).status_code
            == 404
        )
        assert client.patch("/api/loans/2", json={"status": "accepted"}).status_code == 400
