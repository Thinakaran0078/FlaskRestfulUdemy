from conftest import auth_header, register_and_login


def create_store(client, headers, name="Bookstore"):
    return client.post("/store", json={"name": name}, headers=headers).get_json()


def create_item(client, headers, store_id, name="Widget", price=9.99):
    """Item creation is guarded by `@jwt_required(refresh=True)`, so it must
    be called with a *refresh* token, not an access token."""
    return client.post(
        "/item",
        json={"name": name, "price": price, "store_id": store_id},
        headers=headers,
    )


def test_create_item_requires_a_refresh_token(client):
    tokens = register_and_login(client)
    store = create_store(client, auth_header(tokens["access_token"]))

    with_access_token = create_item(client, auth_header(tokens["access_token"]), store["id"])
    assert with_access_token.status_code == 401

    with_refresh_token = create_item(client, auth_header(tokens["refresh_token"]), store["id"])
    assert with_refresh_token.status_code == 201
    body = with_refresh_token.get_json()
    assert body["name"] == "Widget"
    assert body["store"]["id"] == store["id"]


def test_get_item_requires_authentication_and_returns_data(client):
    tokens = register_and_login(client)
    store = create_store(client, auth_header(tokens["access_token"]))
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"]).get_json()

    unauthenticated = client.get(f"/item/{item['id']}")
    assert unauthenticated.status_code == 401

    authenticated = client.get(f"/item/{item['id']}", headers=auth_header(tokens["access_token"]))
    assert authenticated.status_code == 200
    assert authenticated.get_json()["name"] == "Widget"


def test_get_item_returns_404_for_unknown_id(client):
    tokens = register_and_login(client)

    response = client.get("/item/999", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 404


def test_update_existing_item(client):
    tokens = register_and_login(client)
    store = create_store(client, auth_header(tokens["access_token"]))
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"]).get_json()

    update_response = client.put(
        f"/item/{item['id']}",
        json={"name": "Widget Pro", "price": 19.99},
        headers=auth_header(tokens["access_token"]),
    )

    assert update_response.status_code == 200
    body = update_response.get_json()
    assert body["name"] == "Widget Pro"
    assert body["price"] == 19.99


def test_update_missing_item_creates_it(client):
    """PUT on a non-existent id falls back to creating a new item with that id."""
    tokens = register_and_login(client)
    store = create_store(client, auth_header(tokens["access_token"]))

    response = client.put(
        "/item/12345",
        json={"name": "New Item", "price": 1.5, "store_id": store["id"]},
        headers=auth_header(tokens["access_token"]),
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == 12345
    assert body["name"] == "New Item"


def test_delete_item_requires_admin_privilege(client):
    tokens = register_and_login(client)
    store = create_store(client, auth_header(tokens["access_token"]))
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"]).get_json()

    # First user is admin because their numeric id is 1.
    admin_response = client.delete(f"/item/{item['id']}", headers=auth_header(tokens["access_token"]))
    assert admin_response.status_code == 200
    assert admin_response.get_json() == {"message": "Item deleted."}

    second_user = register_and_login(client, username="bob", password="secret")
    store_2 = create_store(client, auth_header(second_user["access_token"]), name="Second Store")
    item_2 = create_item(client, auth_header(second_user["refresh_token"]), store_2["id"], name="Other Widget").get_json()
    forbidden_response = client.delete(f"/item/{item_2['id']}", headers=auth_header(second_user["access_token"]))
    assert forbidden_response.status_code == 401
    assert forbidden_response.get_json()["message"] == "Admin privilege required."


def test_delete_item_requires_authentication(client):
    response = client.delete("/item/1")

    assert response.status_code == 401
