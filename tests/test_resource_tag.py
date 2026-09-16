from conftest import auth_header, register_and_login


def create_store(client, headers, name="Bookstore"):
    return client.post("/store", json={"name": name}, headers=headers).get_json()


def create_item(client, refresh_headers, store_id, name="Widget", price=9.99):
    return client.post(
        "/item",
        json={"name": name, "price": price, "store_id": store_id},
        headers=refresh_headers,
    ).get_json()


def test_create_and_list_tags_for_a_store(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])
    store = create_store(client, headers)

    create_response = client.post(
        f"/store/{store['id']}/tag", json={"name": "Sale"}, headers=headers
    )
    assert create_response.status_code == 201
    tag = create_response.get_json()
    assert tag["name"] == "Sale"

    list_response = client.get(f"/store/{store['id']}/tag", headers=headers)
    assert list_response.status_code == 200
    assert [t["name"] for t in list_response.get_json()] == ["Sale"]


def test_create_tag_does_not_validate_the_store_exists(client):
    """TagInStore.post never calls StoreModel.get_or_404, and SQLite does not
    enforce the store_id foreign key by default, so a tag can be created
    against a non-existent store id without error."""
    tokens = register_and_login(client)

    response = client.post(
        "/store/999/tag", json={"name": "Sale"}, headers=auth_header(tokens["access_token"])
    )

    assert response.status_code == 201
    assert response.get_json()["name"] == "Sale"


def test_get_tag_returns_404_for_unknown_id(client):
    tokens = register_and_login(client)

    response = client.get("/tag/999", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 404


def test_link_and_unlink_tag_to_item(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])
    store = create_store(client, headers)
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"])
    tag = client.post(f"/store/{store['id']}/tag", json={"name": "Sale"}, headers=headers).get_json()

    link_response = client.post(f"/item/{item['id']}/tag/{tag['id']}", headers=headers)
    assert link_response.status_code == 201
    assert any(i["id"] == item["id"] for i in link_response.get_json()["items"])

    unlink_response = client.delete(f"/item/{item['id']}/tag/{tag['id']}", headers=headers)
    assert unlink_response.status_code == 200
    body = unlink_response.get_json()
    assert body["message"] == "Item removed from Tag"
    assert body["tag"]["items"] == []


def test_delete_tag_fails_while_still_linked_to_an_item(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])
    store = create_store(client, headers)
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"])
    tag = client.post(f"/store/{store['id']}/tag", json={"name": "Sale"}, headers=headers).get_json()
    client.post(f"/item/{item['id']}/tag/{tag['id']}", headers=headers)

    response = client.delete(f"/tag/{tag['id']}", headers=headers)

    # Tag.delete only deletes when `not tag.items`; when a tag is still
    # linked it falls through and implicitly returns None. flask-smorest
    # still reports the decorated 202 status with a null body instead of
    # the documented 400 "tag assigned to items" alt-response, and the tag
    # is silently NOT deleted.
    assert response.status_code == 202
    assert response.get_json() is None

    still_there = client.get(f"/tag/{tag['id']}", headers=headers)
    assert still_there.status_code == 200


def test_delete_tag_succeeds_once_unlinked(client):
    tokens = register_and_login(client)
    headers = auth_header(tokens["access_token"])
    store = create_store(client, headers)
    item = create_item(client, auth_header(tokens["refresh_token"]), store["id"])
    tag = client.post(f"/store/{store['id']}/tag", json={"name": "Sale"}, headers=headers).get_json()
    client.post(f"/item/{item['id']}/tag/{tag['id']}", headers=headers)
    client.delete(f"/item/{item['id']}/tag/{tag['id']}", headers=headers)

    response = client.delete(f"/tag/{tag['id']}", headers=headers)

    assert response.status_code == 202
    assert response.get_json() == {"message": "Tag deleted."}


def test_tag_endpoints_require_authentication(client):
    response = client.get("/tag/1")

    assert response.status_code == 401
