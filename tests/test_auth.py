from fastapi.testclient import TestClient
from ..app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/auth/register", json={
        "clientDetails": {
            "idNumber": "1234567890123",
            "cellphoneNumber": "1234567890",
            "email": "test@example.com",
            "name": "Test",
            "surname": "User",
            "password": "securepassword",
            "gender": "male"
        },
        "employerDetails": {
            "name": "Test Company"
        },
        "bankDetails": {
            "bankName": "Test Bank",
            "accountNumber": "123456789",
            "accountType": "savings"
        }
    })
    assert response.status_code == 201
    assert "email" in response.json()