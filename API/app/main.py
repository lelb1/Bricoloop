from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import LocationRow, ToolRow, UserRow, make_engine
from app.models import (
    Loan,
    LoanCreate,
    LoanDecision,
    ReceivedLoan,
    Tool,
    ToolCreate,
    ToolDetail,
    ToolEtatUpdate,
    User,
)


def create_app(*, engine: Engine | None = None) -> FastAPI:
    database = engine if engine is not None else make_engine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if engine is None:
            database.dispose()

    app = FastAPI(title="BricoLoop API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-User-Id"],
    )

    def get_session():
        with Session(database) as session:
            yield session

    DbSession = Annotated[Session, Depends(get_session)]

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        if (
            request.method == "POST"
            and (request.url.path == "/api/tools" or request.url.path.endswith("/loans"))
        ) or (
            request.method == "PATCH"
            and request.url.path.startswith(("/api/tools/", "/api/loans/"))
        ):
            errors = [
                {"field": ".".join(map(str, error["loc"][1:])) or "body", "message": error["msg"]}
                for error in exc.errors()
            ]
            return JSONResponse(status_code=400, content={"detail": errors})
        return await request_validation_exception_handler(request, exc)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Base de données indisponible"})

    @app.post(
        "/api/tools",
        response_model=Tool,
        status_code=201,
        responses={400: {"description": "Champ invalide ou utilisateur inconnu"}},
    )
    def create_tool(
        payload: ToolCreate,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        tool = ToolRow(**payload.model_dump(), ownerId=user_id, status="available")
        session.add(tool)
        session.commit()
        session.refresh(tool)
        return tool

    @app.patch("/api/tools/{tool_id}/etat", response_model=Tool)
    def update_etat(
        tool_id: int,
        payload: ToolEtatUpdate,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        tool = session.get(ToolRow, tool_id)
        if tool is None:
            raise HTTPException(status_code=404, detail="Outil introuvable")
        if tool.ownerId != user_id:
            raise HTTPException(status_code=403, detail="Seul le propriétaire peut modifier l’état")
        tool.etat = payload.etat
        session.commit()
        session.refresh(tool)
        return tool

    @app.post("/api/tools/{tool_id}/loans", response_model=Loan, status_code=201)
    def request_loan(
        tool_id: int,
        payload: LoanCreate,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        tool = session.get(ToolRow, tool_id)
        if tool is None:
            raise HTTPException(status_code=404, detail="Outil introuvable")
        if tool.ownerId == user_id:
            raise HTTPException(status_code=400, detail="toolId : impossible d’emprunter son outil")
        if payload.endDate < payload.startDate:
            raise HTTPException(status_code=400, detail="endDate : antérieure à startDate")
        if payload.startDate < datetime.now(ZoneInfo("Europe/Paris")).date():
            raise HTTPException(status_code=400, detail="startDate : date passée interdite")
        if tool.status != "available":
            raise HTTPException(status_code=400, detail="toolId : outil non disponible")
        loan = LocationRow(
            **payload.model_dump(), toolId=tool_id, borrowerId=user_id, status="pending"
        )
        session.add(loan)
        session.commit()
        session.refresh(loan)
        return loan

    @app.get("/api/loans/received", response_model=list[ReceivedLoan])
    def received_loans(
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        rows = session.execute(
            select(LocationRow, ToolRow.name, UserRow)
            .join(ToolRow, LocationRow.toolId == ToolRow.id)
            .join(UserRow, LocationRow.borrowerId == UserRow.id)
            .where(ToolRow.ownerId == user_id)
            .order_by(LocationRow.id.desc())
        ).all()
        return [
            ReceivedLoan(
                **Loan.model_validate(loan).model_dump(),
                toolName=name,
                borrower=User.model_validate(borrower),
            )
            for loan, name, borrower in rows
        ]

    @app.patch("/api/loans/{loan_id}", response_model=Loan)
    def decide_loan(
        loan_id: int,
        payload: LoanDecision,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        # Verrouille la demande pour éviter deux décisions concurrentes.
        loan = session.scalar(
            select(LocationRow).where(LocationRow.id == loan_id).with_for_update()
        )
        if loan is None:
            raise HTTPException(status_code=404, detail="Demande introuvable")
        tool = session.scalar(select(ToolRow).where(ToolRow.id == loan.toolId).with_for_update())
        if tool.ownerId != user_id:
            raise HTTPException(status_code=403, detail="Seul le propriétaire peut répondre")
        if loan.status != "pending":
            raise HTTPException(status_code=409, detail="La demande n’est plus en attente")
        loan.status = payload.status
        if payload.status == "accepted":
            tool.status = "lent"
        session.commit()
        session.refresh(loan)
        return loan

    @app.get("/api/users", response_model=list[User])
    def list_users(session: DbSession):
        return session.scalars(select(UserRow).order_by(UserRow.id)).all()

    @app.get("/api/tools", response_model=list[Tool])
    def list_tools(session: DbSession):
        return session.scalars(
            select(ToolRow).order_by(ToolRow.status != "available", ToolRow.id)
        ).all()

    @app.get(
        "/api/tools/{tool_id}",
        response_model=ToolDetail,
        summary="Consulter la fiche d’un outil",
        description=(
            "Renvoie le nom, la catégorie, la description et le statut de l’outil, "
            "ainsi que le prénom et le quartier de son propriétaire dans owner."
        ),
        responses={
            404: {
                "description": "Aucun outil ne correspond à cet identifiant",
                "content": {"application/json": {"example": {"detail": "Outil introuvable"}}},
            }
        },
    )
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
