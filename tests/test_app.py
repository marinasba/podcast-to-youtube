import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Podcast" in response.data


def test_generate_without_files(client):
    response = client.post("/generate")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_generate_with_wrong_format(client):
    from io import BytesIO
    response = client.post("/generate", data={
        "video": (BytesIO(b"fake"), "test.avi"),
        "audio": (BytesIO(b"fake"), "test.ogg"),
    }, content_type="multipart/form-data")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "errors" in data
