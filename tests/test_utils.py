import pytest
import asyncio
from app.contacts import _to_model_kwargs
from app.cache import get_user_from_cache


def test_to_model_kwargs():
    payload = {
        "first_name": "Anna",
        "last_name": "Test",
        "email": "a@b.com",
        "phone": "123",
        "extra": "note"
    }
    result = _to_model_kwargs(payload)
    assert result["name"] == "Anna"
    assert result["last_name"] == "Test"
    assert result["email"] == "a@b.com"
    assert result["phone"] == "123"
    assert result["extra"] == "note"


@pytest.mark.asyncio
async def test_get_user_from_cache_empty():
    user = await get_user_from_cache(999)
    assert user is None
