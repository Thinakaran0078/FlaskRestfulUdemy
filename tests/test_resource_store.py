from conftest import auth_header, register_and_login


def test_create_store_requires_authentication(client):
    response = client.post("/store", json={"name": "Bookstore"})

    assert response.status_code == 401


def test_create_and_get_store(client):
    tokens = register_and_login(client)

    create_response = client.post(
        "/store", json={"name": "Bookstore"}, headers=auth_header(tokens["access_token"])
    )
    assert create_response.status_code == 201
    store = create_response.get_json()
    assert store["name"] == "Bookstore"
    assert store["items"] == []
    assert store["tags"] == []

    get_response = client.get(f"/store/{store['id']}", headers=auth_header(tokens["access_token"]))
    assert get_response.status_code == 200
    assert get_response.get_json()["name"] == "Bookstore"


def test_create_store_rejects_duplicate_name(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])

    client.post("/store", json={"name": "Bookstore"}, headers=headers)
    duplicate = client.post("/store", json={"name": "Bookstore"}, headers=headers)

    assert duplicate.status_code == 400
    assert "already exists" in duplicate.get_json()["message"]


def test_get_store_returns_404_for_unknown_id(client):
    tokens = register_and_login(client)

    response = client.get("/store/999", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 404


def test_delete_store_removes_it(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])

    store = client.post("/store", json={"name": "Bookstore"}, headers=headers).get_json()

    delete_response = client.delete(f"/store/{store['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.get_json() == {"message": "Store deleted."}

    get_response = client.get(f"/store/{store['id']}", headers=headers)
    assert get_response.status_code == 404


def test_store_list_supports_search_and_pagination(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])

    for name in ["Bookstore", "Book Nook", "Grocery"]:
        client.post("/store", json={"name": name}, headers=headers)

    search_response = client.get("/store?q=Book", headers=headers)
    assert search_response.status_code == 200
    body = search_response.get_json()
    assert body["total"] == 2
    assert {item["name"] for item in body["items"]} == {"Bookstore", "Book Nook"}

    paginated_response = client.get("/store?per_page=1&page=2", headers=headers)
    assert paginated_response.status_code == 200
    paginated_body = paginated_response.get_json()
    assert paginated_body["page"] == 2
    assert paginated_body["per_page"] == 1
    assert paginated_body["total"] == 3
    assert paginated_body["pages"] == 3
    assert len(paginated_body["items"]) == 1
