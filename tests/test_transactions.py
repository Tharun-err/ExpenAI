import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.main import app
from backend.app.routes.transaction import get_db


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

TEST_DATABASE_URL = DATABASE_URL.rsplit("/", 1)[0] + "/finance_controller_test"

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


def test_create_transaction():
    response = client.post(
        "/transactions/",
        json={
            "description": "Test transaction",
            "amount": 100,
            "type": "expense",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["description"] == "Test transaction"
    assert data["amount"] == 100
    assert data["type"] == "expense"


def test_update_transaction():
    response = client.post(
        "/transactions/",
        json={
            "description": "Original transaction",
            "amount": 200,
            "type": "expense",
        },
    )

    transaction_id = response.json()["id"]

    response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "description": "Updated transaction",
            "amount": 300,
            "type": "expense",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["description"] == "Updated transaction"
    assert data["amount"] == 300


def test_delete_transaction():
    response = client.post(
        "/transactions/",
        json={
            "description": "Transaction to delete",
            "amount": 150,
            "type": "expense",
        },
    )

    transaction_id = response.json()["id"]

    response = client.delete(
        f"/transactions/{transaction_id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Transaction deleted successfully"