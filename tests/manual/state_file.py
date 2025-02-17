"""
This manual test is intended to be used as a stress tester by running many copies on the same host at the same
time to try and create race conditions.
"""

import asyncio
import os

from hlid import hlid

from threatpatrols_action.shared.lib.state import get_state_handler

hlid = str(hlid())
key = "tests/" + hlid.split("-")[0] + "/" + hlid

state_handler = get_state_handler(method="filesystem", state_ttl_seconds=300)

writelock_file = state_handler.key_file(key=key, extension="writelock")
if writelock_file.exists():
    os.unlink(writelock_file)


async def test_ten_thousand_iterations():

    for _ in range(0, 10000):

        data = {"foo": "bar", "this": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "nonce": str(hlid()), "count": 0}

        await state_handler.save_state(key=key, data=data)
        saved_data = await state_handler.load_state(key=key)

        if saved_data != data:
            raise Exception(f"{saved_data=} {data=}")  # provides observability

        assert saved_data == data
        data["count"] = +1


asyncio.run(test_ten_thousand_iterations())
