import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


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