import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("origin", ["http://localhost:5500", "http://127.0.0.1:5500"])
def test_front_can_read_catalogue(make_app, origin):
    with TestClient(make_app()) as client:
        response = client.get("/api/tools", headers={"Origin": origin})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert any(tool["name"] == "Perceuse Bosch" for tool in response.json())


def test_front_can_send_current_user_header(make_app):
    with TestClient(make_app()) as client:
        response = client.options(
            "/api/tools",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-user-id",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_other_origins_not_authorized(make_app):
    with TestClient(make_app()) as client:
        response = client.get("/api/tools", headers={"Origin": "http://example.com"})
        assert "access-control-allow-origin" not in response.headers
