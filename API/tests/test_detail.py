import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_tool_detail_with_owner():
    response = TestClient(create_app()).get("/api/tools/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "ownerId": 1,
        "name": "Perceuse",
        "category": "Perçage",
        "description": "Perceuse avec forets",
        "status": "lent",
        "owner": {"id": 1, "firstName": "Bilal", "district": "Centre"},
    }


@pytest.mark.parametrize("tool_id", [999, 0, -1])
def test_unknown_tool_returns_404(tool_id):
    response = TestClient(create_app()).get(f"/api/tools/{tool_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Outil introuvable"}


def test_detail_in_empty_catalogue():
    response = TestClient(create_app(tools=[])).get("/api/tools/1")
    assert response.status_code == 404


def test_invalid_identifier():
    response = TestClient(create_app()).get("/api/tools/abc")
    assert response.status_code == 422
