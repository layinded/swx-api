from datetime import datetime, timedelta


def test_create_and_validate_api_key(client):
    # Create a key
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    response = client.post(
        "/user/api_keys/",
        json={
            "user_id": "33333333-3333-3333-3333-333333333333",
            "expires_at": expires_at
        },
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 201
    data = response.json()
    key = data["key"]

    # Validate the key
    validate_response = client.get(
        "/user/api_keys/validate",
        headers={"X-API-Key": key}
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["usage_count"] == 1
