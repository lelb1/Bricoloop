from fastapi.testclient import TestClient


def test_owned_tools_and_pending_count_update(make_app):
    with TestClient(make_app()) as client:
        headers = {"X-User-Id": "1"}
        response = client.get("/api/tools/mine", headers=headers)
        assert response.status_code == 200
        rows = response.json()
        assert [r["id"] for r in rows] == [1, 2]
        assert [r["pendingRequests"] for r in rows] == [1, 0]
        assert all(r["ownerId"] == 1 for r in rows)
        client.patch("/api/loans/2", headers=headers, json={"status": "refused"})
        assert client.get("/api/tools/mine", headers=headers).json()[0]["pendingRequests"] == 0
        other = client.get("/api/tools/mine", headers={"X-User-Id": "2"}).json()
        assert [r["id"] for r in other] == [3, 4]
        assert all(r["pendingRequests"] == 0 for r in other)


def test_no_tools_and_unknown_user(make_app):
    with TestClient(make_app(tools=[])) as client:
        assert client.get("/api/tools/mine", headers={"X-User-Id": "1"}).json() == []
        assert client.get("/api/tools/mine", headers={"X-User-Id": "999"}).status_code == 400
