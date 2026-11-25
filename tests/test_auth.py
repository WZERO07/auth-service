

import pytest

from app.models import RefreshToken, User
from app.security import hash_token


def test_read_me(client, login_test_user, db):
    response = client.get("/me", headers={"Authorization": f"Bearer {login_test_user['access_token']}"})
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

def test_register_password_too_short(client):
    response = client.post("/register", json={"email": "test@example.com", "password": "a"})
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
    with pytest.raises(Exception): #noqa: B017
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

def test_register_without_email(client):
    response = client.post("/register", json={"password": "secret"})
    assert response.status_code == 422  # Expect a error



    

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






def test_new_refresh_token_rotation(client, login_test_user, db):

    # Use the refresh token to get a new access token
    response = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 200

    assert "access_token" in response.json()  # Ensure an access token is returned
    assert response.json()["token_type"] == "bearer"  # Ensure the token type is correct

    new_refresh_token = response.json()["refresh_token"]

    # Ensure the new refresh token is different from the old one
    assert new_refresh_token != login_test_user["refresh_token"]

    # Ensure the old refresh token is no longer valid (i.e., it has been rotated)
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(login_test_user["refresh_token"])).first().revoked is True

    #ensure the new refresh token is stored in the database
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(new_refresh_token)).first() is not None

    #ensurte the new refresh token is not revoked
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(new_refresh_token)).first().revoked is False


def test_refresh_token_with_new_token_generated(client, login_test_user):
    # Use the refresh token to get a new access token
    response = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 200

    new_refresh_token = response.json()["refresh_token"]

    # Now, try to use the new refresh token to get another access token
    response = client.post("/refresh", json={"refresh_token": new_refresh_token})
    assert response.status_code == 200  # Expect a successful refresh

    # Ensure the new refresh token is different from the previous one
    assert response.json()["refresh_token"] != new_refresh_token


def test_refresh_token_with_revoked_token(client, login_test_user):
    # Use the refresh token to get a new access token
    response = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 200

    # Now, try to use the old refresh token again
    response = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 401  # Expect an unauthorized error since the old token is revoked


def test_refresh_token_with_invalid_token(client):
    response = client.post("/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401  # Expect an unauthorized error

def test_refresh_token_with_non_existent_json(client):
    response = client.post("/refresh", json={})
    assert response.status_code == 422  # Expect a bad request error




def test_logout_user(client, login_test_user, db):
    # Use the refresh token to logout
    response = client.post("/logout", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 200  # Expect a successful logout
    assert response.json() == {"message": "Logged out successfully"}

    # Ensure the refresh token is revoked in the database and exists
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(login_test_user["refresh_token"])).first() is not None
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(login_test_user["refresh_token"])).first().revoked is True


def test_refresh_token_after_logout(client, login_test_user):
    # Use the refresh token to logout
    client.post("/logout", json={"refresh_token": login_test_user["refresh_token"]})

    # Now, try to use the same refresh token to get a new access token
    response = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})
    assert response.status_code == 401  # Expect an unauthorized error since the token is revoked


def test_logout_only_the_actual_logged_user(client, login_test_user, db):
    # Register and login a second user
    client.post("/register", json={"email": "second_user@example.com", "password": "password"})
    second_user = client.post("/login", json={"email": "second_user@example.com", "password": "password"})
    
    assert second_user.status_code == 200
    assert "refresh_token" in second_user.json()
    data = {"access_token": second_user.json()["access_token"], "refresh_token": second_user.json()["refresh_token"]}
    
    # Use the refresh token to logout the first user
    client.post("/logout", json={"refresh_token": login_test_user["refresh_token"]})

    # Ensure the first user's refresh token is revoked
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(login_test_user["refresh_token"])).first().revoked is True

    # Ensure the second user's refresh token is not revoked
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(data["refresh_token"])).first().revoked is False


def test_logout_only_the_actual_device_from_a_logged_user(client, login_test_user, db):
    # Register and login a second device with same user
    second_device = client.post("/login", json={"email": "test@example.com", "password": "secret"})
    
    assert second_device.status_code == 200
    assert "refresh_token" in second_device.json()
    data = {"access_token": second_device.json()["access_token"], "refresh_token": second_device.json()["refresh_token"]}
    
    # Use the refresh token to logout the device
    client.post("/logout", json={"refresh_token": login_test_user["refresh_token"]})

    # Ensure the first user's device refresh token is revoked
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(login_test_user["refresh_token"])).first().revoked is True

    # Ensure the second user's device refresh token is not revoked
    assert db.query(RefreshToken).filter(RefreshToken.hashed_token == hash_token(data["refresh_token"])).first().revoked is False

    refresh_from_new_device = client.post("/refresh", json={"refresh_token": data["refresh_token"]})  # This should succeed since the second device's token is still valid
    assert refresh_from_new_device.status_code == 200

    refresh_from_revoked_device = client.post("/refresh", json={"refresh_token": login_test_user["refresh_token"]})  # This should fail since the first device's token is revoked
    assert refresh_from_revoked_device.status_code == 401


def test_logout_leaks_no_info_by_comparing_response_for_invalid_and_valid_token(client, login_test_user):
    # Use the refresh token to logout the first user
    response_valid = client.post("/logout", json={"refresh_token": login_test_user["refresh_token"]})
    assert response_valid.status_code == 200  # Expect a successful logout

    # Now, try to logout with an invalid token
    response_invalid = client.post("/logout", json={"refresh_token": "invalid_token"})
    assert response_invalid.status_code == 200  # Expect a successful logout even for invalid token

    # Ensure both responses are the same to not leak information about the validity of the token
    assert response_valid.json() == response_invalid.json() == {"message": "Logged out successfully"}





def test_admin_user_can_access_admin_route_and_retrieve_list_of_users(client, login_test_admin_user,db):

    assert db.query(User).filter(User.role == "admin").first() is not None  # Ensure the user is admin

    response = client.get("/admin/users", headers={"Authorization": f"Bearer {login_test_admin_user['access_token']}"})
    assert response.status_code == 200

    assert len(response.json()) > 0  # Ensure the response contains user data
    assert "email" in response.json()["users"][0]  # Ensure the user data contains email
    assert "id" in response.json()["users"][0]  # Ensure the user data contains id

    assert "password" not in response.json()["users"][0] and "hashed_password" not in response.json()["users"][0]  # Ensure password is not returned


def test_non_admin_user_cannot_access_admin_route(client, login_test_user):
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {login_test_user['access_token']}"})
    assert response.status_code == 403  # Expect a forbidden error for non-admin users


def test_normal_user_cannot_access_admin_route_but_can_access_once_promoted(client, login_test_user, db):
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {login_test_user['access_token']}"})
    assert response.status_code == 403  # Expect a forbidden error for non-admin users

    # Promote the user to admin
    db.query(User).filter(User.email == "test@example.com").update({"role": "admin"})
    db.commit()

    # Now the user should be able to access the admin route
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {login_test_user['access_token']}"})
    assert response.status_code == 200

    #user demotion
    db.query(User).filter(User.email == "test@example.com").update({"role": "user"})
    db.commit()

    #retry to access the admin route after demotion
    response = client.get("/admin/users", headers={"Authorization": f"Bearer {login_test_user['access_token']}"})
    assert response.status_code == 403  # Expect a forbidden error for non-admin users after demotion

def test_role_admin_cannot_be_registered_directly(client, db):
    response = client.post("/register", json={"email": "test@example.com", "password": "password", "role": "admin"})
    assert response.status_code == 201  # Expect a success on register new user but error for trying to register as admin

    assert db.query(User).filter(User.email == "test@example.com").first().role == "user"  # Ensure the role is set to "user" even if "admin" was provided

def test_admin_cannot_call_admin_privileges_whiout_token(client):
    response = client.get("/admin/users")
    assert response.status_code == 401  # Expect an unauthorized error since no token is provided

