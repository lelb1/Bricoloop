from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import ToolRow, UserRow, initialize
from app.main import create_app


def test_persistence_and_seed_does_not_overwrite(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url)
    initialize(engine)
    with Session(engine) as session, session.begin():
        assert session.scalar(select(func.count()).select_from(UserRow)) == 4
        assert session.scalar(select(func.count()).select_from(ToolRow)) == 8
        session.execute(update(ToolRow).where(ToolRow.id == 1).values(name="Perceuse modifiée"))
    engine.dispose()
    restarted = create_engine(url)
    try:
        initialize(restarted)
        with TestClient(create_app(engine=restarted)) as client:
            response = client.get("/api/tools/1")
            assert response.status_code == 200
            assert response.json()["name"] == "Perceuse modifiée"
            assert len(client.get("/api/tools").json()) == 8
    finally:
        restarted.dispose()


def test_database_unavailable_returns_503():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    try:
        with TestClient(create_app(engine=engine)) as client:
            response = client.get("/api/tools")
            assert response.status_code == 503
            assert response.json() == {"detail": "Base de données indisponible"}
    finally:
        engine.dispose()
