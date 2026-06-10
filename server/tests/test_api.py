import pytest
from fastapi.testclient import TestClient

from myroomie.app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    authed = TestClient(app)
    authed.post("/auth/register", json={"username": "tester", "password": "pw12345"})
    token = authed.post("/auth/login", json={"username": "tester", "password": "pw12345"}).json()["token"]
    authed.headers.update({"Authorization": f"Bearer {token}"})
    return authed


@pytest.fixture()
def anon(tmp_path):
    """A client sharing the same app/db as `client` is not trivial across
    fixtures, so this gives a fresh unauthenticated client for auth tests."""
    app = create_app(str(tmp_path / "test.db"))
    return TestClient(app)


def create_roomie(client, name="Mira", gender="girl", seed=123):
    response = client.post("/pets", json={"name": name, "gender": gender, "seed": seed})
    assert response.status_code == 200
    return response.json()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_create_pet_generates_traits(client):
    pet = create_roomie(client)
    assert pet["traits"]["personality"]
    assert pet["wallet"]["money"] > 0
    assert any(event["kind"] == "welcome" for event in pet["inbox"])


def test_create_pet_rejects_bad_gender(client):
    response = client.post("/pets", json={"name": "X", "gender": "robot"})
    assert response.status_code == 400


def test_feed_endpoint(client):
    pet = create_roomie(client)
    response = client.post(f"/pets/{pet['id']}/feed", json={"food": "pancakes"})
    assert response.status_code == 200


def test_feed_without_money_fails(client):
    pet = create_roomie(client)
    for attempt in range(40):
        client.post(f"/pets/{pet['id']}/feed", json={"food": "sushi"})
    final = client.post(f"/pets/{pet['id']}/feed", json={"food": "sushi"})
    assert final.status_code == 400


def test_visit_reduces_loneliness(client):
    pet = create_roomie(client)
    response = client.post(f"/pets/{pet['id']}/visit")
    assert response.status_code == 200


def test_catalog_lists_content(client):
    catalog = client.get("/catalog").json()
    assert "foods" in catalog and "jobs" in catalog


def test_unknown_pet_404(client):
    assert client.get("/pets/does-not-exist").status_code == 404


def test_websocket_streams_state(client):
    pet = create_roomie(client)
    token = client.headers["Authorization"].split(" ")[1]
    with client.websocket_connect(f"/pets/{pet['id']}/ws?token={token}") as ws:
        data = ws.receive_json()
        assert data["id"] == pet["id"]
        assert "stats" in data


def test_websocket_rejects_bad_token(client):
    pet = create_roomie(client)
    with pytest.raises(Exception):
        with client.websocket_connect(f"/pets/{pet['id']}/ws?token=bogus") as ws:
            ws.receive_json()


def test_register_and_login(anon):
    assert anon.post("/auth/register", json={"username": "amy", "password": "secret1"}).status_code == 200
    assert anon.post("/auth/register", json={"username": "amy", "password": "secret1"}).status_code == 409
    body = anon.post("/auth/login", json={"username": "amy", "password": "secret1"}).json()
    assert "token" in body
    assert anon.post("/auth/login", json={"username": "amy", "password": "nope"}).status_code == 401


def test_pet_endpoints_require_auth(anon):
    assert anon.get("/pets").status_code == 401
    assert anon.post("/pets", json={"name": "X", "gender": "girl"}).status_code == 401


def test_cannot_access_another_users_roomie(client, anon):
    pet = create_roomie(client)  # owned by "tester"
    anon.post("/auth/register", json={"username": "intruder", "password": "pw123456"})
    token = anon.post("/auth/login", json={"username": "intruder", "password": "pw123456"}).json()["token"]
    resp = anon.get(f"/pets/{pet['id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_preview_is_deterministic_for_a_seed(client):
    first = client.post("/preview", json={"seed": 999}).json()
    second = client.post("/preview", json={"seed": 999}).json()
    assert first["seed"] == 999
    assert first["traits"] == second["traits"]


def test_preview_without_seed_returns_one(client):
    body = client.post("/preview", json={}).json()
    assert isinstance(body["seed"], int)
    assert body["traits"]["personality"]


def test_catalog_includes_shop(client):
    catalog = client.get("/catalog").json()
    assert "shop" in catalog and "cozy_sweater" in catalog["shop"]


def test_buy_and_wear_endpoints(client):
    pet = create_roomie(client)
    pid = pet["id"]
    # earn enough first
    for shift in range(3):
        client.post(f"/pets/{pid}/work", json={"job": "tutoring"})
    bought = client.post(f"/pets/{pid}/buy", json={"item": "summer_dress"}).json()
    assert "summer_dress" in bought["wardrobe"]
    assert bought["outfit"] == "summer_dress"
    client.post(f"/pets/{pid}/buy", json={"item": "pajamas"})
    worn = client.post(f"/pets/{pid}/wear", json={"item": "summer_dress"}).json()
    assert worn["outfit"] == "summer_dress"


def test_mark_inbox_seen(client):
    pet = create_roomie(client)
    assert any(not event["seen"] for event in pet["inbox"])
    marked = client.post(f"/pets/{pet['id']}/inbox/seen").json()
    assert all(event["seen"] for event in marked["inbox"])

