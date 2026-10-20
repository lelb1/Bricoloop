import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.engine import URL, Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.data import seed_tools, seed_users


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[str] = mapped_column(String(80))
    district: Mapped[str] = mapped_column(String(120))


class ToolRow(Base):
    __tablename__ = "tools"
    id: Mapped[int] = mapped_column(primary_key=True)
    ownerId: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    category: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(20), default="available", index=True)
    owner: Mapped[UserRow] = relationship()


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
        session.add_all(UserRow(**user.model_dump()) for user in seed_users())
        session.flush()
        session.add_all(ToolRow(**tool.model_dump()) for tool in seed_tools())
