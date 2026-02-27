def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"


def test_action_item_validation_and_delete(client):
    # description must be non-empty
    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422

    # pagination params must be within bounds
    r = client.get("/action-items/", params={"skip": -1})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"limit": 0})
    assert r.status_code == 422

    # create a valid item then delete it
    r = client.post("/action-items/", json={"description": "To delete"})
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 204

    # subsequent get should return 404
    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 404


def test_action_items_pagination_and_sorting(client):
    # create multiple action items with descriptions out of lexical order
    payloads = [
        {"description": "Task B"},
        {"description": "Task A"},
        {"description": "Task C"},
    ]
    ids: list[int] = []
    for payload in payloads:
        r = client.post("/action-items/", json=payload)
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])

    # mark one as completed to exercise filtering with sorting
    r = client.put(f"/action-items/{ids[0]}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    # sort by description ascending
    r = client.get("/action-items/", params={"sort": "description"})
    assert r.status_code == 200
    items = r.json()
    assert [item["description"] for item in items] == ["Task A", "Task B", "Task C"]

    # sort by description descending
    r = client.get("/action-items/", params={"sort": "-description"})
    assert r.status_code == 200
    items = r.json()
    assert [item["description"] for item in items] == ["Task C", "Task B", "Task A"]

    # pagination with skip and limit combined with sorting
    r = client.get("/action-items/", params={"sort": "description", "skip": 1, "limit": 1})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["description"] == "Task B"

    # filter completed items with sorting
    r = client.get("/action-items/", params={"completed": True, "sort": "description"})
    assert r.status_code == 200
    items = r.json()
    assert all(item["completed"] is True for item in items)


