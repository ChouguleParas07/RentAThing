from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@app.get("/__test__/boom")
async def boom() -> None:
    raise ExceptionGroup("boom", [RuntimeError("boom")])


def test_register_raw_bytes_returns_422_not_500() -> None:
    payload = b'{"email":"paraschougule1008@gmail.com","full_name":"Paras Ashok Chougule","password":"Paras@1008","phone":"8999834789","city":"","role":"RENTER"}'

    response = client.post(
        "/auth/register",
        content=payload,
        headers={"Content-Type": "application/octet-stream"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"][0]["input"] == payload.decode("utf-8")
    assert body["error_code"] == "VALIDATION_ERROR"


def test_exception_group_returns_json_500() -> None:
    response = client.get("/__test__/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["message"] == "Internal server error"
