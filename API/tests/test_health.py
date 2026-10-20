from fastapi.testclient import TestClient


def test_health(make_app):
    response = TestClient(make_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
