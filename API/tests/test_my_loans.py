from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient


def test_only_my_requests_sorted_by_start_date(make_app):
    with TestClient(make_app()) as client:
        response = client.get("/api/loans/mine", headers={"X-User-Id": "1"})
        assert response.status_code == 200
        rows = response.json()
        assert [r["id"] for r in rows] == [3, 1]
        assert all(r["borrowerId"] == 1 for r in rows)
        assert [r["status"] for r in rows] == ["returned", "accepted"]
        assert all(r["toolName"] for r in rows)
        day = (datetime.now(ZoneInfo("Europe/Paris")).date() + timedelta(days=3)).isoformat()
        created = client.post(
            "/api/tools/5/loans",
            headers={"X-User-Id": "1"},
            json={"startDate": day, "endDate": day},
        )
        assert created.status_code == 201
        mine = client.get("/api/loans/mine", headers={"X-User-Id": "1"}).json()
        assert mine[-1]["id"] == created.json()["id"]
        other = client.get("/api/loans/mine", headers={"X-User-Id": "2"}).json()
        assert all(r["borrowerId"] == 2 for r in other)


def test_empty_and_unknown_profile(make_app):
    with TestClient(make_app()) as client:
        assert client.get("/api/loans/mine", headers={"X-User-Id": "4"}).json() == []
        assert client.get("/api/loans/mine", headers={"X-User-Id": "999"}).status_code == 400
        assert client.get("/api/loans/mine").status_code == 422
