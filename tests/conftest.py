import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db

os.environ["SECRET_KEY"] = "6cc3177715eaac2eb28a094f044340f04ebef58938b39f7e1c33884cccf87759"  # Set a test secret key before it gets the key from .env file for testing

from app.main import app
from app.models import User


@pytest.fixture
def client(db):
    def override_get_db():
        return db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        yield TestingSessionLocal()
    finally:
        TestingSessionLocal().close()
        engine.dispose()

@pytest.fixture
def create_test_user(client):
    response = client.post("/register", json={"email": "test@example.com", "password": "secret"})

    data = response.json()
    return data  # Return the user data in form of dictionary for use in tests


@pytest.fixture
def login_test_user(client, create_test_user):
    response = client.post("/login", json={"email": create_test_user["email"], "password": "secret"})

    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]

    data = {"access_token": access_token, "refresh_token": refresh_token}
    return data


@pytest.fixture
def login_test_admin_user(client,db):
    # Create a normal user
    client.post("/register", json={"email": "admin@example.com", "password": "adminsecret"})

    # Update the user's role to admin
    db.query(User).filter(User.email == "admin@example.com").update({"role": "admin"})
    db.commit()
    
    # Log in as the admin user
    response = client.post("/login", json={"email": "admin@example.com", "password": "adminsecret"})

    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]

    data = {"access_token": access_token, "refresh_token": refresh_token}
    return data
