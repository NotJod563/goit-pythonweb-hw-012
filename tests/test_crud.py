from app import crud, models, schemas


def test_create_contact_direct(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()

    contact_in = schemas.ContactCreate(
        name="Test",
        last_name="Contact",
        email="test@contact.com",
        phone="+1234567890"
    )
    contact = crud.create_contact(db, contact_in, user.id)
    assert contact.name == "Test"
    assert contact.email == "test@contact.com"


def test_get_contact_direct(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()

    contact_in = schemas.ContactCreate(
        name="Direct",
        last_name="Check",
        email="direct@example.com",
        phone="+380991112233"
    )
    contact = crud.create_contact(db, contact_in, user.id)

    fetched = crud.get_contact(db, contact.id, user.id)
    assert fetched is not None
    assert fetched.email == "direct@example.com"

    deleted = crud.delete_contact(db, contact.id, user.id)
    assert deleted is True


def test_update_contact(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()

    contact_in = schemas.ContactCreate(
        name="Old",
        last_name="Name",
        email="updatable@example.com",
        phone="+3800000000"
    )
    contact = crud.create_contact(db, contact_in, user.id)

    updated = crud.update_contact(db, contact.id, user.id, schemas.ContactUpdate(name="New"))
    assert updated.name == "New"


def test_get_contacts(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()
    contacts = crud.get_contacts(db, user.id)
    assert isinstance(contacts, list)


def test_get_contact(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()
    contact = crud.create_contact(db, schemas.ContactCreate(
        name="Direct", last_name="Get", email="direct@get.com", phone="+1234567890"
    ), user.id)

    found = crud.get_contact(db, contact.id, user.id)
    assert found.email == "direct@get.com"


def test_search_contact(db):
    user = db.query(models.User).filter_by(email="contactuser@example.com").first()
    crud.create_contact(db, schemas.ContactCreate(
        name="Anna", last_name="Search", email="anna@search.com", phone="111"
    ), user.id)

    results = crud.search_contacts(db, user.id, query="Ann")
    assert any(c.name == "Anna" for c in results)
