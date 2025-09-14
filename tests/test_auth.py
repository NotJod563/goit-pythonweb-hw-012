from jose import jwt
from app.models import User
from app.config import settings


def test_signup_login_me(client, db):
    signup_data = {
        "email": "user@example.com",
        "password": "password123"
    }

    res = client.post("/auth/signup", json=signup_data)
    assert res.status_code == 201
    user_id = res.json()["id"]

    user = db.query(User).get(user_id)
    user.is_verified = True
    db.commit()

    res = client.post("/auth/login", data={
        "username": signup_data["email"],
        "password": signup_data["password"]
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token

    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == signup_data["email"]


def test_reset_password(client, db):
    signup_data = {
        "email": "reset@example.com",
        "password": "oldpassword"
    }

    res = client.post("/auth/signup", json=signup_data)
    assert res.status_code == 201
    user_id = res.json()["id"]

    user = db.query(User).get(user_id)
    user.is_verified = True
    db.commit()

    res = client.post("/auth/reset/request", json={"email": signup_data["email"]})
    assert res.status_code == 200
    token = res.json()["token"]

    new_password = "newsecurepass"
    res = client.post("/auth/reset/confirm", json={
        "token": token,
        "new_password": new_password
    })
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    res = client.post("/auth/login", data={
        "username": signup_data["email"],
        "password": new_password
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_reset_request_user_not_found(client):
    res = client.post("/auth/reset/request", json={"email": "notfound@example.com"})
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_reset_confirm_invalid_token(client):
    res = client.post("/auth/reset/confirm", json={
        "token": "broken.token.string",
        "new_password": "pass123"
    })
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid or expired token"


def test_reset_confirm_wrong_purpose(client, db):
    signup_data = {
        "email": "wrongpurpose@example.com",
        "password": "oldpass"
    }
    res = client.post("/auth/signup", json=signup_data)
    user_id = res.json()["id"]

    token = jwt.encode(
        {"sub": str(user_id), "purpose": "invalid", "exp": 9999999999},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    res = client.post("/auth/reset/confirm", json={
        "token": token,
        "new_password": "newpass"
    })
    assert res.status_code == 400


def test_verify_email_success(client, db):
    res = client.post("/auth/signup", json={
        "email": "verify@example.com",
        "password": "verify123"
    })
    user_id = res.json()["id"]

    token = jwt.encode({"sub": str(user_id)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    res = client.get(f"/auth/verify?token={token}")
    assert res.status_code == 200
    assert res.json() == "verified"

    user = db.query(User).get(user_id)
    assert user.is_verified


def test_verify_email_no_sub(client):
    token = jwt.encode({}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = client.get(f"/auth/verify?token={token}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid token"


def test_verify_email_broken_token(client):
    res = client.get("/auth/verify?token=abc.def.ghi")
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid token"


def test_verify_email_user_not_found(client):
    token = jwt.encode({"sub": "999999"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    res = client.get(f"/auth/verify?token={token}")
    assert res.status_code == 400
    assert res.json()["detail"] == "Invalid token"


def test_users_me_no_token(client):
    res = client.get("/users/me")
    assert res.status_code == 401


def test_users_me_invalid_token(client):
    res = client.get("/users/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert res.status_code == 401


def test_login_user_not_found(client):
    res = client.post("/auth/login", data={
        "username": "nouser@example.com",
        "password": "somepass"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


def test_login_wrong_password(client, db):
    res = client.post("/auth/signup", json={
        "email": "wrongpass@example.com",
        "password": "correctpass"
    })
    user_id = res.json()["id"]

    user = db.query(User).get(user_id)
    user.is_verified = True
    db.commit()

    res = client.post("/auth/login", data={
        "username": "wrongpass@example.com",
        "password": "wrongpass"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid credentials"


def test_login_email_not_verified(client):
    res = client.post("/auth/signup", json={
        "email": "unverified@example.com",
        "password": "somepass"
    })
    assert res.status_code == 201

    res = client.post("/auth/login", data={
        "username": "unverified@example.com",
        "password": "somepass"
    })
    assert res.status_code == 403
    assert res.json()["detail"] == "Email is not verified"
