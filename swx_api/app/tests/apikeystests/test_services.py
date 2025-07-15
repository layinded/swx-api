from datetime import datetime, timedelta, timezone
from swx_api.app.services.api_keys_service import ApiKeysService
from swx_api.app.models.api_keys import ApiKeysCreate

def test_validate_and_increment_usage(db_session):
    expires = datetime.now(timezone.utc) + timedelta(minutes=1)
    data = ApiKeysCreate(
        user_id="22222222-2222-2222-2222-222222222222",
        expires_at=expires
    )
    api_key = ApiKeysService.create_api_key(db_session, data)

    # Valid key
    success, result = ApiKeysService.validate_and_increment_usage(db_session, api_key.key)
    assert success
    assert result.id == api_key.id

    # Expired key
    api_key.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.add(api_key)
    db_session.commit()

    success, result = ApiKeysService.validate_and_increment_usage(db_session, api_key.key)
    assert not success
    assert result["code"] == "API_KEY_EXPIRED"
