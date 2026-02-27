import pytest


def test_create_and_list_tags(client):
    """Test creating and listing tags."""
    # Create a tag
    r = client.post("/tags/", json={"name": "urgent"})
    assert r.status_code == 201
    tag = r.json()
    assert tag["name"] == "urgent"
    tag_id = tag["id"]

    # List tags
    r = client.get("/tags/")
    assert r.status_code == 200
    tags = r.json()
    assert len(tags) >= 1
    assert any(t["name"] == "urgent" for t in tags)


def test_create_duplicate_tag(client):
    """Test that creating a duplicate tag returns 409."""
    client.post("/tags/", json={"name": "work"})
    r = client.post("/tags/", json={"name": "work"})
    assert r.status_code == 409


def test_get_tag(client):
    """Test getting a single tag."""
    r = client.post("/tags/", json={"name": "personal"})
    tag_id = r.json()["id"]

    r = client.get(f"/tags/{tag_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "personal"


def test_get_nonexistent_tag(client):
    """Test getting a non-existent tag returns 404."""
    r = client.get("/tags/99999")
    assert r.status_code == 404


def test_delete_tag(client):
    """Test deleting a tag."""
    r = client.post("/tags/", json={"name": "temporary"})
    tag_id = r.json()["id"]

    r = client.delete(f"/tags/{tag_id}")
    assert r.status_code == 204

    r = client.get(f"/tags/{tag_id}")
    assert r.status_code == 404


def test_add_tag_to_note(client):
    """Test adding a tag to a note."""
    # Create a note
    r = client.post("/notes/", json={"title": "Test Note", "content": "Test content"})
    note_id = r.json()["id"]

    # Add a tag to the note
    r = client.post(f"/notes/{note_id}/tags", json={"name": "important"})
    assert r.status_code == 200
    note = r.json()
    assert len(note["tags"]) >= 1
    assert any(t["name"] == "important" for t in note["tags"])


def test_remove_tag_from_note(client):
    """Test removing a tag from a note."""
    # Create a note with a tag
    r = client.post("/notes/", json={"title": "Tag Test", "content": "Content"})
    note_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/tags", json={"name": "review"})
    tag_id = r.json()["tags"][0]["id"]

    # Remove the tag
    r = client.delete(f"/notes/{note_id}/tags/{tag_id}")
    assert r.status_code == 200
    note = r.json()
    assert not any(t["id"] == tag_id for t in note["tags"])


def test_note_with_tags_includes_tags(client):
    """Test that getting a note includes its tags."""
    # Create a note and add tags
    r = client.post("/notes/", json={"title": "Multi Tag", "content": "Content"})
    note_id = r.json()["id"]

    client.post(f"/notes/{note_id}/tags", json={"name": "tag1"})
    client.post(f"/notes/{note_id}/tags", json={"name": "tag2"})

    # Get the note
    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 200
    note = r.json()
    tag_names = [t["name"] for t in note["tags"]]
    assert "tag1" in tag_names
    assert "tag2" in tag_names


def test_tag_pagination(client):
    """Test tag pagination."""
    # Create multiple tags
    for i in range(5):
        client.post("/tags/", json={"name": f"paginate{i}"})

    r = client.get("/tags/?skip=0&limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/tags/?skip=2&limit=2")
    assert r.status_code == 200
    assert len(r.json()) == 2
