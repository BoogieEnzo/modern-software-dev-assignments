from sqlalchemy import create_engine, inspect

from backend.app.models import Base


def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


def test_notes_search_with_larger_dataset(client):
    for i in range(100):
        r = client.post(
            "/notes/",
            json={"title": f"Note {i}", "content": f"Content {i}"},
        )
        assert r.status_code == 201, r.text

    r = client.post(
        "/notes/",
        json={"title": "Special", "content": "Needle content"},
    )
    assert r.status_code == 201, r.text

    r = client.get("/notes/search/", params={"q": "Needle"})
    assert r.status_code == 200
    items = r.json()
    assert any("Needle" in note["content"] for note in items)


def test_indexes_exist_for_notes_and_action_items():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)

    note_indexes = inspector.get_indexes("notes")
    note_index_columns = {tuple(idx["column_names"]) for idx in note_indexes}
    assert ("title",) in note_index_columns

    action_indexes = inspector.get_indexes("action_items")
    action_index_columns = {tuple(idx["column_names"]) for idx in action_indexes}
    assert ("completed",) in action_index_columns
