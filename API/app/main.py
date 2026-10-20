from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, get_args
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import LocationRow, RatingRow, ToolRow, UserRow, make_engine
from app.models import (
    BorrowedLoan,
    Category,
    Loan,
    LoanCreate,
    LoanDecision,
    OwnedTool,
    Rating,
    RatingCreate,
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

    frontend = Path(__file__).resolve().parents[2] / "front" / "bricoloop"
    app.mount("/web", StaticFiles(directory=frontend), name="web")

    @app.get("/", include_in_schema=False)
    def website():
        return RedirectResponse("/web/bricoloop-catalogue.html")

    def get_session():
        with Session(database) as session:
            yield session

    DbSession = Annotated[Session, Depends(get_session)]

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        if (
            request.method == "POST"
            and (
                request.url.path == "/api/tools"
                or request.url.path.endswith("/loans")
                or request.url.path.startswith("/api/loans/")
            )
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

    def accepted_loans(session: Session, tool_id: int):
        # Lecture verrouillée : tient compte des acceptations qui viennent d’être validées.
        return session.scalars(
            select(LocationRow)
            .where(LocationRow.toolId == tool_id, LocationRow.status == "accepted")
            .order_by(LocationRow.id)
            .with_for_update()
        ).all()

    def reject_overlap(loans, start, end):
        if any(loan.startDate <= end and loan.endDate >= start for loan in loans):
            raise HTTPException(status_code=409, detail="Les dates chevauchent un prêt accepté")

    @app.post("/api/tools/{tool_id}/loans", response_model=Loan, status_code=201)
    def request_loan(
        tool_id: int,
        payload: LoanCreate,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        tool = session.scalar(select(ToolRow).where(ToolRow.id == tool_id).with_for_update())
        if tool is None:
            raise HTTPException(status_code=404, detail="Outil introuvable")
        if tool.ownerId == user_id:
            raise HTTPException(status_code=400, detail="toolId : impossible d’emprunter son outil")
        if payload.endDate < payload.startDate:
            raise HTTPException(status_code=400, detail="endDate : antérieure à startDate")
        if payload.startDate < datetime.now(ZoneInfo("Europe/Paris")).date():
            raise HTTPException(status_code=400, detail="startDate : date passée interdite")
        bookings = accepted_loans(session, tool_id)
        reject_overlap(bookings, payload.startDate, payload.endDate)
        # Un outil prêté peut être réservé pour une autre période.
        if tool.status == "unavailable" or (tool.status == "lent" and not bookings):
            raise HTTPException(status_code=400, detail="toolId : outil non disponible")
        loan = LocationRow(
            **payload.model_dump(), toolId=tool_id, borrowerId=user_id, status="pending"
        )
        session.add(loan)
        session.commit()
        session.refresh(loan)
        return loan

    @app.get("/api/loans/mine", response_model=list[BorrowedLoan])
    def my_loans(
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        rows = session.execute(
            select(LocationRow, ToolRow.name)
            .join(ToolRow, LocationRow.toolId == ToolRow.id)
            .where(LocationRow.borrowerId == user_id)
            .order_by(LocationRow.startDate, LocationRow.id)
        ).all()
        return [
            BorrowedLoan(**Loan.model_validate(loan).model_dump(), toolName=name)
            for loan, name in rows
        ]

    @app.get("/api/loans/received", response_model=list[ReceivedLoan])
    def received_loans(
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        rows = session.execute(
            select(LocationRow, ToolRow.name, UserRow, RatingRow.score)
            .join(ToolRow, LocationRow.toolId == ToolRow.id)
            .join(UserRow, LocationRow.borrowerId == UserRow.id)
            .outerjoin(RatingRow, RatingRow.loanId == LocationRow.id)
            .where(ToolRow.ownerId == user_id)
            .order_by(LocationRow.id.desc())
        ).all()
        return [
            ReceivedLoan(
                **Loan.model_validate(loan).model_dump(),
                toolName=name,
                borrower=User.model_validate(borrower),
                rating=score,
            )
            for loan, name, borrower, score in rows
        ]

    @app.patch("/api/loans/{loan_id}", response_model=Loan)
    def decide_loan(
        loan_id: int,
        payload: LoanDecision,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        tool_id = session.scalar(select(LocationRow.toolId).where(LocationRow.id == loan_id))
        if tool_id is None:
            raise HTTPException(status_code=404, detail="Demande introuvable")
        # Même ordre de verrouillage pour toutes les opérations : outil, puis locations.
        tool = session.scalar(select(ToolRow).where(ToolRow.id == tool_id).with_for_update())
        loan = session.scalar(
            select(LocationRow).where(LocationRow.id == loan_id).with_for_update()
        )
        if tool.ownerId != user_id:
            raise HTTPException(status_code=403, detail="Seul le propriétaire peut répondre")
        if loan.status != "pending":
            raise HTTPException(status_code=409, detail="La demande n’est plus en attente")
        if payload.status == "accepted":
            reject_overlap(accepted_loans(session, tool.id), loan.startDate, loan.endDate)
        loan.status = payload.status
        if payload.status == "accepted":
            tool.status = "lent"
        session.commit()
        session.refresh(loan)
        return loan

    @app.patch("/api/loans/{loan_id}/return", response_model=Loan)
    def return_loan(
        loan_id: int,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        tool_id = session.scalar(select(LocationRow.toolId).where(LocationRow.id == loan_id))
        if tool_id is None:
            raise HTTPException(status_code=404, detail="Demande introuvable")
        tool = session.scalar(select(ToolRow).where(ToolRow.id == tool_id).with_for_update())
        loan = session.scalar(
            select(LocationRow).where(LocationRow.id == loan_id).with_for_update()
        )
        if tool.ownerId != user_id:
            raise HTTPException(
                status_code=403, detail="Seul le propriétaire peut déclarer le retour"
            )
        if loan.status != "accepted":
            raise HTTPException(status_code=409, detail="Seul un prêt accepté peut être rendu")
        loan.status = "returned"
        tool.status = "available"
        session.commit()
        session.refresh(loan)
        return loan

    @app.post("/api/loans/{loan_id}/rating", response_model=Rating, status_code=201)
    def rate_borrower(
        loan_id: int,
        payload: RatingCreate,
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        tool_id = session.scalar(select(LocationRow.toolId).where(LocationRow.id == loan_id))
        if tool_id is None:
            raise HTTPException(status_code=404, detail="Prêt introuvable")
        tool = session.scalar(select(ToolRow).where(ToolRow.id == tool_id).with_for_update())
        loan = session.scalar(
            select(LocationRow).where(LocationRow.id == loan_id).with_for_update()
        )
        if tool.ownerId != user_id:
            raise HTTPException(
                status_code=403, detail="Seul le propriétaire peut noter l’emprunteur"
            )
        if loan.status != "returned":
            raise HTTPException(status_code=409, detail="Le prêt doit être rendu avant de noter")
        existing = session.scalar(
            select(RatingRow).where(RatingRow.loanId == loan_id).with_for_update()
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="Ce prêt a déjà une note")
        rating = RatingRow(loanId=loan_id, score=payload.score)
        session.add(rating)
        session.commit()
        session.refresh(rating)
        return rating

    @app.get("/api/tools/mine", response_model=list[OwnedTool])
    def my_tools(
        session: DbSession,
        user_id: Annotated[int, Header(alias="X-User-Id", gt=0)],
    ):
        if session.get(UserRow, user_id) is None:
            raise HTTPException(status_code=400, detail="X-User-Id : utilisateur inconnu")
        counts = (
            select(LocationRow.toolId.label("tool_id"), func.count().label("pending"))
            .where(LocationRow.status == "pending")
            .group_by(LocationRow.toolId)
            .subquery()
        )
        rows = session.execute(
            select(ToolRow, func.coalesce(counts.c.pending, 0))
            .outerjoin(counts, counts.c.tool_id == ToolRow.id)
            .where(ToolRow.ownerId == user_id)
            .order_by(ToolRow.id)
        ).all()
        return [
            OwnedTool(**Tool.model_validate(tool).model_dump(), pendingRequests=count)
            for tool, count in rows
        ]

    @app.get("/api/users", response_model=list[User])
    def list_users(session: DbSession):
        return session.scalars(select(UserRow).order_by(UserRow.id)).all()

    @app.get("/api/tools", response_model=list[Tool])
    def list_tools(session: DbSession, category: str | None = None, q: str = ""):
        query = select(ToolRow)
        if category is not None:
            if category not in get_args(Category):
                raise HTTPException(status_code=400, detail="category : catégorie inconnue")
            query = query.where(ToolRow.category == category)
        tools = session.scalars(query.order_by(ToolRow.status != "available", ToolRow.id)).all()
        keyword = q.strip().casefold()
        return [
            tool
            for tool in tools
            if not keyword
            or keyword in tool.name.casefold()
            or keyword in (tool.description or "").casefold()
        ]

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
