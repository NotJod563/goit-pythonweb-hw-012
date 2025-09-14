from app import crud, schemas, models


def test_get_contacts_empty(client, db, token):
    res = client.get("/contacts/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json() == []


def test_create_contact(client, db, token):
    contact_data = {
        "name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+1234567890"
    }
    res = client.post("/contacts/", json=contact_data, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "John"
    assert data["email"] == "john@example.com"


def test_delete_contact(client, db, token):
    contact_data = {
        "name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone": "+19876543210"
    }
    res = client.post("/contacts/", json=contact_data, headers={"Authorization": f"Bearer {token}"})
    contact_id = res.json()["id"]

    res = client.delete(f"/contacts/{contact_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 204


def test_check_duplicates_name_conflict(client, db, token):
    contact = {
        "name": "John",
        "last_name": "Smith",
        "email": "unique1@example.com",
        "phone": "123456",
    }
    client.post("/contacts/", json=contact, headers={"Authorization": f"Bearer {token}"})

    contact_conflict = {
        "name": "John",
        "last_name": "Smith",
        "email": "unique2@example.com",
        "phone": "654321",
    }
    res = client.post("/contacts/", json=contact_conflict, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 409
    assert "already exists" in res.text


def test_delete_contact_not_found(client, token):
    res = client.delete("/contacts/99999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404
