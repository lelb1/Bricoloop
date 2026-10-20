import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import CheckConstraint, Date, ForeignKey, String, create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.data import seed_locations, seed_tools, seed_users


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "utilisateur"
    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[str] = mapped_column(String(60))
    district: Mapped[str] = mapped_column(String(60))


class ToolRow(Base):
    __tablename__ = "outil"
    __table_args__ = (
        CheckConstraint("LENGTH(name) BETWEEN 2 AND 60"),
        CheckConstraint(
            "category IN ('Perçage','Jardinage','Peinture','Nettoyage','Mesure','Autre')"
        ),
        CheckConstraint("status IN ('available','lent','unavailable')"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    ownerId: Mapped[int] = mapped_column(ForeignKey("utilisateur.id"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    category: Mapped[str] = mapped_column(String(20))
    etat: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="available", server_default="available", index=True
    )
    owner: Mapped[UserRow] = relationship()


class LocationRow(Base):
    __tablename__ = "location"
    __table_args__ = (
        CheckConstraint("endDate >= startDate"),
        CheckConstraint("status IN ('pending','accepted','refused','returned')"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    toolId: Mapped[int] = mapped_column(ForeignKey("outil.id"))
    borrowerId: Mapped[int] = mapped_column(ForeignKey("utilisateur.id"))
    startDate: Mapped[date] = mapped_column(Date)
    endDate: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")


def database_url() -> URL:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "bricoloop"),
        query={"charset": "utf8mb4"},
    )


def make_engine() -> Engine:
    return create_engine(database_url(), pool_pre_ping=True)


def initialize(engine: Engine, *, demo: bool = True) -> None:
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    Base.metadata.create_all(engine)
    if not demo:
        return
    with Session(engine) as session, session.begin():
        # Ne jamais réinsérer le seed dans une base déjà utilisée.
        if session.scalar(select(UserRow.id).limit(1)) is not None:
            return
        if session.scalar(select(ToolRow.id).limit(1)) is not None:
            return
        if session.scalar(select(LocationRow.id).limit(1)) is not None:
            return
        session.add_all(UserRow(**user.model_dump()) for user in seed_users())
        session.flush()
        session.add_all(ToolRow(**tool.model_dump()) for tool in seed_tools())
        session.flush()
        session.add_all(LocationRow(**location) for location in seed_locations())
