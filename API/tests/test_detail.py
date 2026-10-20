import pytest
from fastapi.testclient import TestClient


def test_tool_detail_with_owner(make_app):
    response = TestClient(make_app()).get("/api/tools/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "ownerId": 1,
        "name": "Perceuse Bosch",
        "category": "Perçage",
        "description": "Perceuse à percussion 750 W",
        "status": "available",
        "owner": {"id": 1, "firstName": "Rida", "district": "Centre"},
    }


@pytest.mark.parametrize("tool_id", [999, 0, -1])
def test_unknown_tool_returns_404(tool_id, make_app):
    response = TestClient(make_app()).get(f"/api/tools/{tool_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Outil introuvable"}


def test_detail_in_empty_catalogue(make_app):
    response = TestClient(make_app(tools=[])).get("/api/tools/1")
    assert response.status_code == 404


def test_invalid_identifier(make_app):
    response = TestClient(make_app()).get("/api/tools/abc")
    assert response.status_code == 422


def test_nullable_description(make_app):
    response = TestClient(make_app()).get("/api/tools/7")
    assert response.status_code == 200
    assert response.json()["description"] is None


def test_unknown_id_between_existing_tools(make_app):
    from app.models import Tool

    tools = [Tool(id=i, ownerId=1, name=f"Outil {i}", category="Autre") for i in (1, 3)]
    with TestClient(make_app(tools=tools)) as client:
        assert client.get("/api/tools/1").status_code == 200
        response = client.get("/api/tools/2")
        assert response.status_code == 404
        assert response.json() == {"detail": "Outil introuvable"}
        assert client.get("/api/tools/3").status_code == 200
