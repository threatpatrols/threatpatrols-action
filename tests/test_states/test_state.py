import pytest

from threatpatrols_action.shared.lib.hlid import HLID
from threatpatrols_action.shared.lib.state import get_state_handler


@pytest.mark.asyncio(loop_scope="session")
async def test_01():
    state_handler = get_state_handler("filesystem")

    hlid = str(HLID())
    key = "tests/" + hlid.split("-")[0] + "/" + hlid

    for _ in range(0, 1000):

        data = {"foo": "bar", "this": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "nonce": str(HLID()), "count": 0}

        await state_handler.save_state(key=key, data=data)
        saved_data = await state_handler.load_state(key=key)
        assert saved_data == data

        data["count"] = +1
