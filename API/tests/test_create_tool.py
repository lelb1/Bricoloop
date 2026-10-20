import pytest
from fastapi.testclient import TestClient


def test_create_tool_is_owned_available_and_persisted(make_app):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "2"},
            json={
                "name": "  Marteau  ",
                "category": "Autre",
                "description": "Manche bois",
            },
        )
        assert response.status_code == 201
        tool = response.json()
        assert tool == {
            "id": 9,
            "ownerId": 2,
            "name": "Marteau",
            "category": "Autre",
            "description": "Manche bois",
            "status": "available",
        }
        detail = client.get(f"/api/tools/{tool['id']}").json()
        assert detail["owner"]["firstName"] == "Marc"
        assert tool in client.get("/api/tools").json()
        second = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={
                "name": "Scie",
                "category": "Autre",
            },
        )
        assert second.status_code == 201
        assert second.json()["id"] != tool["id"]
        assert second.json()["description"] is None


@pytest.mark.parametrize("name", ["ab", "x" * 60])
@pytest.mark.parametrize("description", [None, "", "x" * 300])
def test_valid_boundaries(make_app, name, description):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={
                "name": name,
                "category": "Perçage",
                "description": description,
            },
        )
        assert response.status_code == 201


@pytest.mark.parametrize(
    "changes,field",
    [
        ({"name": ""}, "name"),
        ({"name": "x"}, "name"),
        ({"name": "x" * 61}, "name"),
        ({"name": "   "}, "name"),
        ({"name": None}, "name"),
        ({"name": 42}, "name"),
        ({"category": "Inconnue"}, "category"),
        ({"category": None}, "category"),
        ({"description": "x" * 301}, "description"),
        ({"description": 42}, "description"),
        ({"ownerId": 3}, "ownerId"),
        ({"status": "lent"}, "status"),
        ({"id": 99}, "id"),
    ],
)
def test_invalid_fields_do_not_insert(make_app, changes, field):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={
                "name": "Marteau",
                "category": "Autre",
                **changes,
            },
        )
        assert response.status_code == 400
        assert any(error["field"] == field for error in response.json()["detail"])
        assert len(client.get("/api/tools").json()) == 8


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"category": "Autre"}, "name"),
        ({"name": "Scie"}, "category"),
    ],
)
def test_required_fields(make_app, payload, field):
    with TestClient(make_app()) as client:
        response = client.post("/api/tools", headers={"X-User-Id": "1"}, json=payload)
        assert response.status_code == 400
        assert response.json()["detail"][0]["field"] == field


@pytest.mark.parametrize(
    "headers",
    [{}, {"X-User-Id": "abc"}, {"X-User-Id": "0"}, {"X-User-Id": "-1"}, {"X-User-Id": "999"}],
)
def test_current_user_required(make_app, headers):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools", headers=headers, json={"name": "Scie", "category": "Autre"}
        )
        assert response.status_code == 400
        assert "X-User-Id" in str(response.json())
        assert len(client.get("/api/tools").json()) == 8


def test_invalid_json(make_app):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1", "Content-Type": "application/json"},
            content="{",
        )
        assert response.status_code == 400


@pytest.mark.parametrize(
    "category", ["Perçage", "Jardinage", "Peinture", "Nettoyage", "Mesure", "Autre"]
)
def test_all_allowed_categories(make_app, category):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={"name": "Outil", "category": category},
        )
        assert response.status_code == 201
        assert response.json()["category"] == category
        assert response.json()["description"] is None


@pytest.mark.parametrize("length,status", [(60, 201), (61, 400)])
def test_accented_name_length_counts_characters(make_app, length, status):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={"name": "é" * length, "category": "Autre"},
        )
        assert response.status_code == status


@pytest.mark.parametrize("length,status", [(300, 201), (301, 400)])
def test_accented_description_length_counts_characters(make_app, length, status):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/tools",
            headers={"X-User-Id": "1"},
            json={"name": "Outil", "category": "Autre", "description": "é" * length},
        )
        assert response.status_code == status
