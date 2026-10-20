from fastapi.testclient import TestClient


def test_website_and_script_served_by_api(make_app):
    with TestClient(make_app()) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "bricoloop-catalogue.html" in str(page.url)
        assert 'src="catalogue.js"' in page.text
        script = client.get("/web/catalogue.js")
        assert script.status_code == 200
        assert "location.origin" in script.text
