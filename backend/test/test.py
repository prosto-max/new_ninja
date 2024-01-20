import json
import pytest
from uuid import uuid4


async def test_create_user(client, get_user_from_database):
    user_data = {
        "name": "Kostya"
    }
    resp = client.post("/user/", data=json.dumps(user_data))
    data_from_resp = resp.json()
    assert resp.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert users_from_db["is_active"] is True
    users_from_db = await get_user_from_database(data_from_resp["users_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])
    assert users_from_db["name"] == user_data["name"]
    assert users_from_db["is_active"] is True
    assert str(users_from_db["user_id"]) == data_from_resp["user_id"]