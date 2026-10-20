import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "q,ids",
    [
        ("BOSCH", [1]),
        ("percussion", [1]),
        ("KÄRCHER", [4]),
        ("introuvable", []),
        ("%", []),
        ("", [1, 2, 3, 5, 6, 7, 4, 8]),
        ("  bosch  ", [1]),
    ],
)
def test_search_name_description_case_and_empty(make_app, q, ids):
    with TestClient(make_app()) as client:
        response = client.get("/api/tools", params={"q": q})
        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == ids


def test_search_combines_with_category_and_ignores_category_text(make_app):
    with TestClient(make_app()) as client:
        assert client.get("/api/tools?q=Bosch&category=Jardinage").json() == []
        assert client.get("/api/tools?q=Bosch&category=Perçage").json()[0]["id"] == 1
        assert client.get("/api/tools?q=Autre").json() == []
        assert client.get("/api/tools?q=visseuse").json()[0]["description"] is None


def test_unicode_casefold_search(make_app):
    from app.models import Tool

    with TestClient(
        make_app(tools=[Tool(id=9, ownerId=1, name="Straße", category="Autre")])
    ) as client:
        response = client.get("/api/tools", params={"q": "STRASSE"})
        assert response.status_code == 200
        assert [t["id"] for t in response.json()] == [9]
