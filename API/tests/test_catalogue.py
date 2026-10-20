from fastapi.testclient import TestClient


def test_catalogue_fields(make_app):
    response = TestClient(make_app()).get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) == 8
    for tool in tools:
        assert {"id", "name", "category", "status"} <= tool.keys()
        assert tool["name"]
        assert tool["category"]
        assert tool["status"] in {"available", "lent", "unavailable"}


def test_available_tools_first(make_app):
    tools = TestClient(make_app()).get("/api/tools").json()
    availability = [tool["status"] != "available" for tool in tools]
    assert availability == sorted(availability)
    assert any(availability) and not all(availability)


def test_empty_catalogue(make_app):
    response = TestClient(make_app(tools=[])).get("/api/tools")
    assert response.status_code == 200
    assert response.json() == []

