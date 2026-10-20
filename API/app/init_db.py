"""Création explicite de la base et du schéma, sans suppression de données."""
from sqlalchemy import create_engine

from app.database import database_url, initialize, make_engine


def main() -> None:
    url = database_url()
    server = create_engine(url._replace(database=None), pool_pre_ping=True)
    try:
        with server.begin() as connection:
            name = server.dialect.identifier_preparer.quote_identifier(url.database)
            connection.exec_driver_sql(
                f"CREATE DATABASE IF NOT EXISTS {name} CHARACTER SET utf8mb4"
            )
    finally:
        server.dispose()
    engine = make_engine()
    try:
        initialize(engine)
    finally:
        engine.dispose()
    print("Base initialisée ; les données existantes ont été conservées.")


if __name__ == "__main__":
    main()
