import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import LocationRow, ToolRow, initialize
from app.main import create_app


@pytest.fixture
def make_app():
    engines = []

    def factory(*, tools=None):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        engines.append(engine)
        initialize(engine)
        if tools is not None:
            with Session(engine) as session, session.begin():
                session.query(LocationRow).delete()
                session.query(ToolRow).delete()
                session.add_all(ToolRow(**tool.model_dump()) for tool in tools)
        return create_app(engine=engine)

    yield factory
    for engine in engines:
        engine.dispose()
