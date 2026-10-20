import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "category,ids",
    [
        ("Perçage", [1, 7]),
        ("Jardinage", [2, 6]),
        ("Peinture", [3]),
        ("Nettoyage", [4]),
        ("Mesure", [5]),
        ("Autre", [8]),
    ],
)
def test_filter_only_selected_category(make_app, category, ids):
    with TestClient(make_app()) as client:
        response = client.get("/api/tools", params={"category": category})
        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == ids
        assert all(t["category"] == category for t in response.json())


def test_unknown_and_empty_results(make_app):
    with TestClient(make_app()) as client:
        assert client.get("/api/tools?category=inconnue").status_code == 400
    with TestClient(make_app(tools=[])) as client:
        assert client.get("/api/tools?category=Autre").json() == []
