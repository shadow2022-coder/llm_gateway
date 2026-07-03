from app.db import get_session_factory
from app.models import APIKey


def test_ui_homepage_renders(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "FIR Gateway Console" in response.text
    assert "Create Dev API Key" in response.text


def test_ui_can_create_api_key_in_development(client) -> None:
    response = client.post("/ui/api-keys", json={"owner": "browser-user"})

    assert response.status_code == 200
    body = response.json()
    assert body["owner"] == "browser-user"
    assert body["raw_key"].startswith("sk-")

    session_factory = get_session_factory()
    with session_factory() as session:
        api_key = session.get(APIKey, body["id"])
        assert api_key is not None
        assert api_key.owner == "browser-user"
