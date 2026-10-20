from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import LocationRow, initialize
from app.main import create_app


def test_history_filters_and_sorts_newest_first():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    initialize(engine)
    try:
        with Session(engine) as session, session.begin():
            for i, status, month in [
                (4, "accepted", 3),
                (5, "returned", 2),
                (6, "refused", 5),
                (7, "pending", 6),
            ]:
                session.add(
                    LocationRow(
                        id=i,
                        toolId=1,
                        borrowerId=2,
                        startDate=date(2030, month, 1),
                        endDate=date(2030, month, 2),
                        status=status,
                    )
                )
        with TestClient(create_app(engine=engine)) as client:
            response = client.get("/api/tools/1/history", headers={"X-User-Id": "1"})
            assert response.status_code == 200
            rows = response.json()
            assert [r["id"] for r in rows] == [4, 5]
            assert [r["status"] for r in rows] == ["accepted", "returned"]
            assert all(r["borrower"]["firstName"] == "Marc" for r in rows)
            assert all(r["toolId"] == 1 for r in rows)
    finally:
        engine.dispose()


def test_history_access_and_empty_list(make_app):
    with TestClient(make_app()) as client:
        assert client.get("/api/tools/2/history", headers={"X-User-Id": "1"}).json() == []
        assert client.get("/api/tools/4/history", headers={"X-User-Id": "1"}).status_code == 403
        assert client.get("/api/tools/999/history", headers={"X-User-Id": "1"}).status_code == 404
        assert client.get("/api/tools/4/history").status_code == 422
