from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "phone_number": "1234567890",
        "first_name": "Test",
        "last_name": "User",
        "id_number": "1234567890123",
        "gender": "male",
        "password": "securepassword",
        "confirm_password": "securepassword"
    })
    assert response.status_code == 201
    assert "email" in response.json()