

import pytest

from app.models import RefreshToken, User
from app.security import hash_token


def test_read_me(client, login_test_user, db):
    response = client.get("/me", headers={"Authorization": f"Bearer {login_test_user[0]}"})
    assert response.status_code == 200

    email_retrieved = response.json()["email"]
    email_in_db = db.query(User).first().email

    assert email_retrieved == email_in_db

def test_read_me_with_invalid_token(client):
    response = client.get("/me", headers={"Authorization": "Bearer invalid_token"})
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

def test_register_user(client, db):
    response = client.post("/register", json={"email": "test@example.com", "password": "secret"})

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "test@example.com"
    assert "password" not in data and "hashed_password" not in data  # Ensure password is not returned

    found_user = db.query(User).filter(User.email == "test@example.com").first()
    assert found_user is not None
    assert found_user.hashed_password.startswith("$2b$")  # Ensure password is not stored in plain text

def test_register_user_with_existing_email(client, db):
    # First, register a user
    client.post("/register", json={"email": "test@example.com", "password": "secret"})

    assert db.query(User).filter(User.email == "test@example.com").first() is not None

    # Then, try to register another user with the same email
    response = client.post("/register", json={"email": "test@example.com", "password": "another_secret"})
    assert response.status_code == 409  # Expect a conflict error


    

def test_login_user_success(client, db):
    # First, register a user
    client.post("/register", json={"email": "test@example.com", "password": "secret"})

    # Then, try to login with the correct credentials
    response = client.post("/login", json={"email": "test@example.com", "password": "secret"})
    assert response.status_code == 200  # Expect a successful login

    assert "access_token" in response.json()  # Ensure an access token is returned
    assert "refresh_token" in response.json()  # Ensure a refresh token is returned
    assert response.json()["token_type"] == "bearer"  # Ensure the token type is correct

    raw_token_in_response = response.json()["refresh_token"]
    assert raw_token_in_response is not None  # Ensure the token in the response

    stored_row = db.query(RefreshToken).first()
    hashed_token_in_db = stored_row.hashed_token
    assert hashed_token_in_db == hash_token(raw_token_in_response)  # Ensure the token is hashed in the database

    assert hashed_token_in_db != raw_token_in_response  # Ensure the token is not stored in plain text


def test_login_user_wrong_password(client):
    # First, register a user
    client.post("/register", json={"email": "test@example.com", "password": "secret"})

    # Then, try to login with the wrong password
    response = client.post("/login", json={"email": "test@example.com", "password": "wrong_secret"})
    assert response.status_code == 401  # Expect an unauthorized error

def test_login_user_wrong_email(client):
    # First, register a user
    client.post("/register", json={"email": "test@example.com", "password": "secret"})

    # Then, try to login with the wrong email
    response = client.post("/login", json={"email": "wrong@example.com", "password": "secret"})
    assert response.status_code == 401  # Expect an unauthorized error