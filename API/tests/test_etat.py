import pytest
from fastapi.testclient import TestClient


def test_profiles_and_physical_condition_are_persisted(make_app):
    with TestClient(make_app()) as client:
        profiles = client.get("/api/users")
        assert profiles.status_code == 200
        assert profiles.json()[1] == {"id": 2, "firstName": "Marc", "district": "Gare"}
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "2"},
            json={
                "name": "Scie",
                "category": "Autre",
                "etat": "Bon état, traces d’usage",
            },
        )
        assert response.status_code == 201
        tool = response.json()
        assert tool["etat"] == "Bon état, traces d’usage"
        assert client.get(f"/api/tools/{tool['id']}").json()["etat"] == tool["etat"]
        assert tool in client.get("/api/tools").json()


@pytest.mark.parametrize("etat,status", [(None, 201), ("é" * 300, 201), ("x" * 301, 400)])
def test_physical_condition_validation(make_app, etat, status):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={
                "name": "Scie",
                "category": "Autre",
                "etat": etat,
            },
        )
        assert response.status_code == status
        if status == 400:
            assert response.json()["detail"][0]["field"] == "etat"
