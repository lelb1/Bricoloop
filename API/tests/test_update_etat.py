import pytest
from fastapi.testclient import TestClient


def test_owner_updates_condition_without_changing_other_fields(make_app):
    with TestClient(make_app()) as client:
        before = client.get("/api/tools/1").json()
        response = client.patch(
            "/api/tools/1/etat", headers={"X-User-Id": "1"}, json={"etat": "Usagé mais fonctionnel"}
        )
        assert response.status_code == 200
        after = client.get("/api/tools/1").json()
        assert after == {**before, "etat": "Usagé mais fonctionnel"}
        assert (
            next(t for t in client.get("/api/tools").json() if t["id"] == 1)["etat"]
            == after["etat"]
        )
        assert (
            client.patch(
                "/api/tools/1/etat", headers={"X-User-Id": "1"}, json={"etat": None}
            ).json()["etat"]
            is None
        )


@pytest.mark.parametrize(
    "tool_id,user,payload,status",
    [
        (1, "2", {"etat": "Bon"}, 403),
        (999, "1", {"etat": "Bon"}, 404),
        (1, "1", {"etat": "x" * 301}, 400),
        (1, "1", {}, 400),
        (1, "1", {"etat": "Bon", "status": "lent"}, 400),
    ],
)
def test_invalid_update_does_not_change_tool(make_app, tool_id, user, payload, status):
    with TestClient(make_app()) as client:
        before = client.get("/api/tools/1").json()
        response = client.patch(
            f"/api/tools/{tool_id}/etat", headers={"X-User-Id": user}, json=payload
        )
        assert response.status_code == status
        assert client.get("/api/tools/1").json() == before


def test_update_requires_profile(make_app):
    with TestClient(make_app()) as client:
        assert client.patch("/api/tools/1/etat", json={"etat": "Bon"}).status_code == 400


def test_browser_can_patch(make_app):
    with TestClient(make_app()) as client:
        response = client.options(
            "/api/tools/1/etat",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "content-type,x-user-id",
            },
        )
        assert response.status_code == 200
