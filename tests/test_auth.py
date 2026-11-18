

import pytest

from app.models import User


def test_read_me(client):
    response = client.get("/me")
    assert response.status_code == 401

def test_register_with_no_valid_email(client):
    response = client.post("/register", json={"email": "invalid_email", "password": "password"})
    assert response.status_code == 422

def test_register_with_no_password(client):
    response = client.post("/register", json={"email": "test@example.com"})
    assert response.status_code == 422

def test_db_stores_user(db):
    user = User(email="test@example.com", hashed_password="not_a_real_hash")
    db.add(user)
    db.commit()

    found_user = db.query(User).filter(User.email == "test@example.com").first()
    assert found_user is not None #check if the user was stored in the database
    assert found_user.role == "user"

def test_two_users_with_same_email_should_fail(db):
    user1 = User(email="test@example.com", hashed_password="not_a_real_hash")
    db.add(user1)
    db.commit()

    user2 = User(email="test@example.com", hashed_password="not_a_real_hash")
    db.add(user2)
    with pytest.raises(Exception):
        db.commit()  # This should raise an exception due to unique constraint on email
    db.rollback()  # Rollback the session to clean up after the failed commit


    