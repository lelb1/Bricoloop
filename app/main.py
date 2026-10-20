from fastapi import FastAPI, HTTPException

from app.data import seed_tools, seed_users
from app.models import Tool, ToolDetail


def create_app(
    *, tools: list[Tool] | None = None
) -> FastAPI:
    app = FastAPI(title="BricoLoop API")

    app.state.tools = seed_tools() if tools is None else list(tools)
    app.state.users = seed_users()

    @app.get("/api/tools", response_model=list[Tool])
    def list_tools() -> list[Tool]:
        return sorted(app.state.tools, key=lambda tool: tool.status != "available")

    @app.get("/api/tools/{tool_id}", response_model=ToolDetail)
    def get_tool(tool_id: int) -> ToolDetail:
        tool = next((tool for tool in app.state.tools if tool.id == tool_id), None)
        if tool is None:
            raise HTTPException(status_code=404, detail="Outil introuvable")
        owner = next(user for user in app.state.users if user.id == tool.ownerId)
        return ToolDetail(**tool.model_dump(), owner=owner)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
