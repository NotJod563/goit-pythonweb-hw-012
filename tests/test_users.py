from unittest.mock import patch
from app.models import User


def test_get_current_user(client, db, token):
    res = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "email" in res.json()


@patch("app.users.cu.upload")
def test_upload_avatar_mocked(mock_upload, client, db, token):
    mock_upload.return_value = {"secure_url": "https://mocked.url/avatar.png"}

    file_data = {"file": ("avatar.png", b"imagebytes", "image/png")}
    res = client.post("/users/me/avatar", files=file_data, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["avatar_url"] == "https://mocked.url/avatar.png"


def test_set_default_avatar(client, db, admin_token):
    user = db.query(User).filter_by(email="contactuser@example.com").first()
    res = client.post(
        "/users/avatar/default",
        params={"user_id": user.id},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert res.json()["avatar_url"].startswith("http")


def test_update_user_role(client, db, admin_token):
    user = db.query(User).filter_by(email="contactuser@example.com").first()
    assert user.role != "admin"

    res = client.patch(
        f"/users/{user.id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert res.json()["email"] == user.email
