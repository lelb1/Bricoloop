from fastapi.testclient import TestClient

from app.main import create_app


def test_catalogue_fields():
    response = TestClient(create_app()).get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) == 8
    for tool in tools:
        assert {"id", "name", "category", "status"} <= tool.keys()
        assert tool["name"]
        assert tool["category"]
        assert tool["status"] in {"available", "lent", "unavailable"}


def test_available_tools_first():
    tools = TestClient(create_app()).get("/api/tools").json()
    availability = [tool["status"] != "available" for tool in tools]
    assert availability == sorted(availability)
    assert any(availability) and not all(availability)


def test_empty_catalogue():
    response = TestClient(create_app(tools=[])).get("/api/tools")
    assert response.status_code == 200
    assert response.json() == []


def test_demo_data():
    app = create_app()
    assert len(app.state.users) == 4
    assert len({tool.category for tool in app.state.tools}) >= 3
    user_ids = {user.id for user in app.state.users}
    assert all(tool.ownerId in user_ids for tool in app.state.tools)
