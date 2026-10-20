from fastapi import FastAPI

from app.data import seed_tools, seed_users
from app.models import Tool


def create_app(
    *, tools: list[Tool] | None = None
) -> FastAPI:
    app = FastAPI(title="BricoLoop API")

    app.state.tools = seed_tools() if tools is None else list(tools)
    app.state.users = seed_users()

    @app.get("/api/tools", response_model=list[Tool])
    def list_tools() -> list[Tool]:
        return sorted(app.state.tools, key=lambda tool: tool.status != "available")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
