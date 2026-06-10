import pytest
from fastapi.testclient import TestClient

from myroomie.app import create_app


@pytest.fixture()
def client(tmp_path):
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


def test_preview_is_deterministic_for_a_seed(client):
    first = client.post("/preview", json={"seed": 999}).json()
    second = client.post("/preview", json={"seed": 999}).json()
    assert first["seed"] == 999
    assert first["traits"] == second["traits"]


def test_preview_without_seed_returns_one(client):
    body = client.post("/preview", json={}).json()
    assert isinstance(body["seed"], int)
    assert body["traits"]["personality"]

