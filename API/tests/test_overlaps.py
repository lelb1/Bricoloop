from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import LocationRow, ToolRow, initialize
from app.main import create_app


@pytest.fixture
def scheduled_client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    initialize(engine)
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    with Session(engine) as session, session.begin():
        session.add(
            LocationRow(
                id=4,
                toolId=1,
                borrowerId=2,
                startDate=today + timedelta(days=10),
                endDate=today + timedelta(days=15),
                status="accepted",
            )
        )
        session.get(ToolRow, 1).status = "lent"
    with TestClient(create_app(engine=engine)) as client:
        yield client, engine, today
    engine.dispose()


@pytest.mark.parametrize(
    "start,end,status",
    [
        (12, 14, 409),
        (9, 11, 409),
        (14, 17, 409),
        (9, 17, 409),
        (10, 15, 409),
        (15, 15, 409),
        (10, 10, 409),
        (16, 18, 201),
        (7, 9, 201),
    ],
)
def test_request_respects_inclusive_dates(scheduled_client, start, end, status):
    client, engine, today = scheduled_client
    response = client.post(
        "/api/tools/1/loans",
        headers={"X-User-Id": "3"},
        json={
            "startDate": (today + timedelta(days=start)).isoformat(),
            "endDate": (today + timedelta(days=end)).isoformat(),
        },
    )
    assert response.status_code == status
    with Session(engine) as session:
        requests = session.scalars(select(LocationRow).where(LocationRow.borrowerId == 3)).all()
        assert len(requests) == (1 if status == 201 else 0)
    if status == 409:
        assert "chevauche" in response.json()["detail"]


def test_conflict_between_pending_requests_checked_at_acceptance(make_app):
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    payload = {
        "startDate": (today + timedelta(days=20)).isoformat(),
        "endDate": (today + timedelta(days=22)).isoformat(),
    }
    with TestClient(make_app()) as client:
        ids = [
            client.post(
                "/api/tools/1/loans", headers={"X-User-Id": str(user)}, json=payload
            ).json()["id"]
            for user in (2, 3)
        ]
        assert (
            client.patch(
                f"/api/loans/{ids[0]}", headers={"X-User-Id": "1"}, json={"status": "accepted"}
            ).status_code
            == 200
        )
        assert (
            client.patch(
                f"/api/loans/{ids[1]}", headers={"X-User-Id": "1"}, json={"status": "accepted"}
            ).status_code
            == 409
        )
        received = client.get("/api/loans/received", headers={"X-User-Id": "1"}).json()
        assert next(r for r in received if r["id"] == ids[1])["status"] == "pending"
        assert (
            client.patch(
                f"/api/loans/{ids[1]}", headers={"X-User-Id": "1"}, json={"status": "refused"}
            ).status_code
            == 200
        )


def test_adjacent_request_can_be_accepted(scheduled_client):
    client, _, today = scheduled_client
    day = (today + timedelta(days=16)).isoformat()
    response = client.post(
        "/api/tools/1/loans", headers={"X-User-Id": "3"}, json={"startDate": day, "endDate": day}
    )
    assert response.status_code == 201
    assert (
        client.patch(
            f"/api/loans/{response.json()['id']}",
            headers={"X-User-Id": "1"},
            json={"status": "accepted"},
        ).status_code
        == 200
    )


@pytest.mark.parametrize("existing_status", ["pending", "refused", "returned"])
def test_only_accepted_loans_block_dates(scheduled_client, existing_status):
    client, engine, today = scheduled_client
    with Session(engine) as session, session.begin():
        session.get(LocationRow, 4).status = existing_status
        session.get(ToolRow, 1).status = "available"
    day = (today + timedelta(days=12)).isoformat()
    assert (
        client.post(
            "/api/tools/1/loans",
            headers={"X-User-Id": "3"},
            json={"startDate": day, "endDate": day},
        ).status_code
        == 201
    )


def test_other_tools_do_not_block_dates(scheduled_client):
    client, _, today = scheduled_client
    day = (today + timedelta(days=12)).isoformat()
    assert (
        client.post(
            "/api/tools/2/loans",
            headers={"X-User-Id": "3"},
            json={"startDate": day, "endDate": day},
        ).status_code
        == 201
    )


def test_lent_without_schedule_remains_unavailable(scheduled_client):
    client, engine, today = scheduled_client
    with Session(engine) as session, session.begin():
        session.get(LocationRow, 4).status = "returned"
    day = (today + timedelta(days=16)).isoformat()
    assert (
        client.post(
            "/api/tools/1/loans",
            headers={"X-User-Id": "3"},
            json={"startDate": day, "endDate": day},
        ).status_code
        == 400
    )
