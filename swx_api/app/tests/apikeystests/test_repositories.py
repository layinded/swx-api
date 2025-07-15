from datetime import datetime, timedelta, timezone
from swx_api.app.repositories.api_keys_repository import ApiKeysRepository
from swx_api.app.models.api_keys import ApiKeysCreate

def test_create_and_get_api_key(db_session):
    # Create
    expires = datetime.now(timezone.utc) + timedelta(days=1)
    data = ApiKeysCreate(
        user_id="11111111-1111-1111-1111-111111111111",
        expires_at=expires
    )
    api_key = ApiKeysRepository.create_api_key(db_session, data)

    assert api_key.id is not None
    assert api_key.usage_count == 0

    # Retrieve by key
    found = ApiKeysRepository.get_api_key_by_key(db_session, api_key.key)
    assert found.id == api_key.id

    # Increment usage
    ApiKeysRepository.increment_usage_count(db_session, found)
    assert found.usage_count == 1
