def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


def test_note_validation_and_delete(client):
    # title and content must be non-empty
    r = client.post("/notes/", json={"title": "", "content": "content"})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "title", "content": ""})
    assert r.status_code == 422

    # pagination params must be within bounds
    r = client.get("/notes/", params={"skip": -1})
    assert r.status_code == 422

    r = client.get("/notes/", params={"limit": 0})
    assert r.status_code == 422

    # create a valid note then delete it
    r = client.post("/notes/", json={"title": "To delete", "content": "temp"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204

    # subsequent get should return 404
    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404


def test_notes_pagination_and_sorting(client):
    # create multiple notes with titles out of lexical order
    payloads = [
        {"title": "B note", "content": "b"},
        {"title": "A note", "content": "a"},
        {"title": "C note", "content": "c"},
    ]
    for payload in payloads:
        r = client.post("/notes/", json=payload)
        assert r.status_code == 201, r.text

    # sort by title ascending
    r = client.get("/notes/", params={"sort": "title"})
    assert r.status_code == 200
    items = r.json()
    assert [item["title"] for item in items] == ["A note", "B note", "C note"]

    # sort by title descending
    r = client.get("/notes/", params={"sort": "-title"})
    assert r.status_code == 200
    items = r.json()
    assert [item["title"] for item in items] == ["C note", "B note", "A note"]

    # pagination with skip and limit combined with sorting
    r = client.get("/notes/", params={"sort": "title", "skip": 1, "limit": 1})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["title"] == "B note"

    # invalid sort field should fall back to default and still succeed
    r = client.get("/notes/", params={"sort": "nonexistent"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 3


