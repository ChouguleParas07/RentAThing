import pytest
import random
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.enums import UserRole

# Use pytest-asyncio or anyio for the event loop
pytestmark = pytest.mark.anyio


def import_time_uuid() -> str:
    return str(uuid.uuid4())[:8]


async def test_full_auth_flow_success() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register a new user
        email = f"user_{import_time_uuid()}@example.com"
        phone = "".join(random.choices("0123456789", k=10))

        reg_payload = {
            "email": email,
            "phone": phone,
            "city": "New York",
            "full_name": "Test User",
            "password": "Password123",
            "role": UserRole.RENTER.value,
        }

        response = await client.post("/auth/register", json=reg_payload)
        assert response.status_code == 201
        data = response.json()
        assert "verification_code" in data
        verification_code = data["verification_code"]

        # 2. Verify email
        verify_payload = {
            "email": email,
            "code": verification_code,
        }
        response = await client.post("/auth/verify-email", json=verify_payload)
        assert response.status_code == 200
        assert response.json() == {"message": "Email verified successfully"}

        # 3. Login
        login_payload = {
            "email": email,
            "password": reg_payload["password"],
        }
        response = await client.post("/auth/login", json=login_payload)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        access_token = token_data["access_token"]

        # 4. Get current user profile (using bearer token)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == email
        assert profile["phone"] == reg_payload["phone"]
        assert profile["city"] == reg_payload["city"]
        assert profile["full_name"] == reg_payload["full_name"]
        assert profile["role"] == reg_payload["role"]
        assert profile["is_active"] is True
        assert profile["is_verified"] is True
