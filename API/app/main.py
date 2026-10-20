from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import ToolRow, make_engine
from app.models import Tool, ToolDetail


def create_app(*, engine: Engine | None = None) -> FastAPI:
    database = engine if engine is not None else make_engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if engine is None:
            database.dispose()

    app = FastAPI(title="BricoLoop API", lifespan=lifespan)

    def get_session():
        with Session(database) as session:
            yield session

    DbSession = Annotated[Session, Depends(get_session)]

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"detail": "Base de données indisponible"})

    @app.get("/api/tools", response_model=list[Tool])
    def list_tools(session: DbSession):
        return session.scalars(
            select(ToolRow).order_by(ToolRow.status != "available", ToolRow.id)
        ).all()

    @app.get("/api/tools/{tool_id}", response_model=ToolDetail)
    def get_tool(tool_id: int, session: DbSession):
        tool = session.scalar(
            select(ToolRow).options(joinedload(ToolRow.owner)).where(ToolRow.id == tool_id)
        )
        if tool is None:
            raise HTTPException(status_code=404, detail="Outil introuvable")
        return tool

    @app.get("/health")
    def health(session: DbSession) -> dict[str, str]:
        session.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
