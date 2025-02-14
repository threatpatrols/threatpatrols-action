import pytest

from threatpatrols_action.shared.lib.hlid import hlid
from threatpatrols_action.shared.lib.state import get_state_handler


@pytest.mark.asyncio(loop_scope="session")
async def test_01():
    state_handler = get_state_handler("filesystem")

    hlid_str = str(hlid())
    key = "tests/" + hlid_str.split("-")[0] + "/" + hlid_str

    for _ in range(0, 1000):

        data = {"foo": "bar", "this": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "nonce": str(hlid()), "count": 0}

        await state_handler.save_state(key=key, data=data)
        saved_data = await state_handler.load_state(key=key)
        assert saved_data == data

        data["count"] = +1
