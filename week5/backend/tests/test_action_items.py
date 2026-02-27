def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1


def test_filter_action_items_by_completed(client):
    first = client.post("/action-items/", json={"description": "First"})
    second = client.post("/action-items/", json={"description": "Second"})

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    first_item = first.json()
    second_item = second.json()

    complete = client.put(f"/action-items/{first_item['id']}/complete")
    assert complete.status_code == 200

    r = client.get("/action-items", params={"completed": "true"})
    assert r.status_code == 200
    completed_items = r.json()
    assert len(completed_items) == 1
    assert completed_items[0]["id"] == first_item["id"]
    assert completed_items[0]["completed"] is True

    r = client.get("/action-items", params={"completed": "false"})
    assert r.status_code == 200
    incomplete_items = r.json()
    assert len(incomplete_items) == 1
    assert incomplete_items[0]["id"] == second_item["id"]
    assert incomplete_items[0]["completed"] is False

    r = client.get("/action-items")
    assert r.status_code == 200
    all_items = r.json()
    assert len(all_items) == 2


def test_bulk_complete_marks_items_and_filters(client):
    ids = []
    for desc in ["One", "Two", "Three"]:
        r = client.post("/action-items/", json={"description": desc})
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])

    bulk = client.post("/action-items/bulk-complete", json=[ids[0], ids[2]])
    assert bulk.status_code == 200, bulk.text
    completed = bulk.json()
    returned_ids = {item["id"] for item in completed}
    assert returned_ids == {ids[0], ids[2]}
    assert all(item["completed"] is True for item in completed)

    r = client.get("/action-items", params={"completed": "true"})
    assert r.status_code == 200
    done_items = r.json()
    done_ids = {item["id"] for item in done_items}
    assert done_ids == {ids[0], ids[2]}

    r = client.get("/action-items", params={"completed": "false"})
    assert r.status_code == 200
    pending_items = r.json()
    pending_ids = {item["id"] for item in pending_items}
    assert pending_ids == {ids[1]}


def test_bulk_complete_rolls_back_on_missing_id(client):
    r1 = client.post("/action-items/", json={"description": "Do A"})
    r2 = client.post("/action-items/", json={"description": "Do B"})
    assert r1.status_code == 201, r1.text
    assert r2.status_code == 201, r2.text

    id1 = r1.json()["id"]

    bulk = client.post("/action-items/bulk-complete", json=[id1, 9999])
    assert bulk.status_code == 400

    r = client.get("/action-items", params={"completed": "true"})
    assert r.status_code == 200
    completed_items = r.json()
    assert completed_items == []
