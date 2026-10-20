import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("score", [1, 5])
def test_owner_can_rate_returned_loan_once(make_app, score):
    with TestClient(make_app()) as client:
        headers = {"X-User-Id": "3"}
        response = client.post("/api/loans/3/rating", headers=headers, json={"score": score})
        assert response.status_code == 201
        assert response.json()["loanId"] == 3
        assert response.json()["score"] == score
        rows = client.get("/api/loans/received", headers=headers).json()
        assert next(r for r in rows if r["id"] == 3)["rating"] == score
        assert (
            client.post("/api/loans/3/rating", headers=headers, json={"score": score}).status_code
            == 409
        )


@pytest.mark.parametrize("score", [0, 6, 1.5, "5", True, None])
def test_invalid_scores(make_app, score):
    with TestClient(make_app()) as client:
        response = client.post(
            "/api/loans/3/rating", headers={"X-User-Id": "3"}, json={"score": score}
        )
        assert response.status_code == 400
        assert response.json()["detail"][0]["field"] == "score"


@pytest.mark.parametrize(
    "loan,user,status", [(3, "1", 403), (1, "2", 409), (2, "1", 409), (999, "1", 404)]
)
def test_ownership_return_and_known_loan_required(make_app, loan, user, status):
    with TestClient(make_app()) as client:
        assert (
            client.post(
                f"/api/loans/{loan}/rating", headers={"X-User-Id": user}, json={"score": 5}
            ).status_code
            == status
        )


def test_profile_and_score_required(make_app):
    with TestClient(make_app()) as client:
        assert client.post("/api/loans/3/rating", json={"score": 5}).status_code == 400
        assert (
            client.post("/api/loans/3/rating", headers={"X-User-Id": "3"}, json={}).status_code
            == 400
        )
