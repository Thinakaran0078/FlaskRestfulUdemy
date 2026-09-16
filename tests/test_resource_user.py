from conftest import auth_header, register_and_login


def test_register_rejects_duplicate_username(client):
    first = client.post("/register", json={"username": "alice", "password": "secret"})
    assert first.status_code == 201

    duplicate = client.post("/register", json={"username": "alice", "password": "other"})
    assert duplicate.status_code == 409


def test_register_requires_username_and_password(client):
    missing_password = client.post("/register", json={"username": "alice"})
    assert missing_password.status_code == 422

    missing_username = client.post("/register", json={"password": "secret"})
    assert missing_username.status_code == 422


def test_login_rejects_wrong_password(client):
    client.post("/register", json={"username": "alice", "password": "secret"})

    response = client.post("/login", json={"username": "alice", "password": "wrong"})

    assert response.status_code == 401
    assert response.get_json()["message"] == "Invalid credentials."


def test_login_rejects_unknown_user(client):
    response = client.post("/login", json={"username": "ghost", "password": "secret"})

    assert response.status_code == 401


def test_get_user_requires_authentication(client):
    tokens = register_and_login(client)

    unauthenticated = client.get("/user/1")
    assert unauthenticated.status_code == 401

    authenticated = client.get("/user/1", headers=auth_header(tokens["access_token"]))
    assert authenticated.status_code == 200
    body = authenticated.get_json()
    assert body["username"] == "alice"
    assert "password" not in body


def test_get_user_returns_404_for_unknown_id(client):
    tokens = register_and_login(client)

    response = client.get("/user/999", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 404


def test_delete_user_removes_the_account(client):
    tokens = register_and_login(client)

    delete_response = client.delete("/user/1", headers=auth_header(tokens["access_token"]))
    assert delete_response.status_code == 200
    assert delete_response.get_json() == {"message": "User deleted."}

    get_response = client.get("/user/1", headers=auth_header(tokens["access_token"]))
    assert get_response.status_code == 404


def test_refresh_issues_a_new_non_fresh_access_token(client):
    tokens = register_and_login(client)

    response = client.post("/refresh", headers=auth_header(tokens["refresh_token"]))

    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_refresh_rejects_access_token(client):
    tokens = register_and_login(client)

    response = client.post("/refresh", headers=auth_header(tokens["access_token"]))

    assert response.status_code == 401


def test_logout_revokes_the_access_token(client):
    tokens = register_and_login(client)

    logout_response = client.post("/logout", headers=auth_header(tokens["access_token"]))
    assert logout_response.status_code == 200
    assert logout_response.get_json() == {"message": "Successfully logged out."}

    reuse_response = client.get("/user/1", headers=auth_header(tokens["access_token"]))
    assert reuse_response.status_code == 401
    assert reuse_response.get_json()["error"] == "token_revoked"


def test_protected_endpoint_without_token_is_rejected(client):
    response = client.get("/user/1")

    assert response.status_code == 401
    assert response.get_json()["error"] == "authorization_required"
