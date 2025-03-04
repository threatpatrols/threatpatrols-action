"""
This manual test is intended to be used as a stress tester by running many copies on the same host at the same
time to try and create race conditions.
"""

import asyncio
import os
from pathlib import Path

from hlid import HLID

from threatpatrols_action.shared.lib.state import get_state_handler

COLLISION_HLID = "20250202-0000-0000-0000-aaabbbcccddd"
state_handler = get_state_handler(method="filesystem", state_ttl_seconds=300)


async def test_ten_thousand_iterations(hlid=COLLISION_HLID):

    extension = "test"
    key = "tests/" + hlid.split("-")[0] + "/" + hlid

    leftover_previous_writelock_file = Path(str(state_handler.key_file(key=key, extension=extension)) + ".writelock")

    if leftover_previous_writelock_file.exists():
        os.unlink(leftover_previous_writelock_file)

    for _ in range(0, 10000):

        data = {"foo": "bar", "this": [1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "nonce": str(HLID()), "count": 0}

        await state_handler.save_state(key=key, data=data, extension=extension)
        saved_data = await state_handler.load_state(key=key, extension=extension)

        if saved_data != data:
            raise Exception(f"{saved_data=} {data=}")  # provides observability

        assert saved_data == data
        data["count"] = +1


asyncio.run(test_ten_thousand_iterations())
