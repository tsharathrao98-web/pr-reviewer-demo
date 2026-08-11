import os
import tempfile

import pytest

import db as db_module


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp()
    db_module.DB_PATH = path
    import app as app_module

    app_module.init_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client
    os.close(fd)
    os.unlink(path)


def test_create_and_list_task(client):
    resp = client.post("/tasks", json={"title": "write tests"})
    assert resp.status_code == 201

    resp = client.get("/tasks")
    assert resp.status_code == 200
    titles = [t["title"] for t in resp.get_json()["items"]]
    assert "write tests" in titles


def test_create_task_requires_title(client):
    resp = client.post("/tasks", json={"title": "  "})
    assert resp.status_code == 400
