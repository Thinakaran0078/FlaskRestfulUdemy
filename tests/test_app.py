def test_index_returns_welcome_message(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Welcome to API page"}


def test_user_can_register_and_login(client):
    register_response = client.post(
        "/register",
        json={"username": "alice", "password": "secret"},
    )

    assert register_response.status_code == 201
    assert register_response.get_json() == {"message": "User created successfully."}

    login_response = client.post(
        "/login",
        json={"username": "alice", "password": "secret"},
    )

    assert login_response.status_code == 200
    data = login_response.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_store_creation_requires_authentication(client):
    unauthorized_response = client.post("/store", json={"name": "Bookstore"})

    assert unauthorized_response.status_code == 401

    client.post("/register", json={"username": "bob", "password": "secret"})
    login_response = client.post("/login", json={"username": "bob", "password": "secret"})
    token = login_response.get_json()["access_token"]

    authorized_response = client.post(
        "/store",
        json={"name": "Bookstore"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert authorized_response.status_code == 201
    assert authorized_response.get_json()["name"] == "Bookstore"
