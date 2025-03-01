import os
from uuid import uuid4

from hlid import HLID

from threatpatrols_action.shared.lib.substitutions import dict_value_substitutions, string_substitutions


def test_substitutions01():

    value = "hello {cruel} world"
    substitutions = {"cruel": "happy"}

    response = string_substitutions(value, substitutions)
    assert response == "hello happy world"


def test_substitutions02():

    value = "hello { cruel } world"  # << bad spaces around token
    substitutions = {"cruel": "happy"}

    response = string_substitutions(value, substitutions)
    assert "happy" not in response
    assert "{ cruel }" in response


def test_substitutions03():

    task_id = str(HLID())

    value = "hello {task_id_prefix} world"
    substitutions = {"task_id": task_id}

    task_id_prefix = task_id.split("-")[0]

    response = string_substitutions(value, substitutions)
    assert response == f"hello {task_id_prefix} world"


def test_substitutions04():

    env_key = f"TEST_{str(uuid4().hex)[0:8].upper()}"
    env_value = str(HLID())
    os.environ[env_key] = env_value

    value = "hello ${" + env_key + "} world"

    response = string_substitutions(value)
    assert "$" not in response
    assert "{" not in response
    assert "}" not in response
    assert env_value in response


def test_substitutions05():

    task_id = str(HLID())
    another_task_id = str(HLID())

    env_value = str(HLID())
    os.environ["TEST_ENV_BEEP"] = env_value

    value = "hello {task_id_prefix} world; this has ${TEST_ENV_BEEP}  an extra space; and this is {another} thing"
    substitutions = {"task_id": task_id, "another": another_task_id}

    task_id_prefix = task_id.split("-")[0]
    response = string_substitutions(value, substitutions)

    assert f"hello {task_id_prefix} world" in response
    assert f"this has {env_value}  an extra space" in response
    assert f"and this is {another_task_id} thing" in response


def test_substitutions06():

    task_id = str(HLID())
    substitutions = {"task_id": task_id}
    data = {"foo": "this is {task_id} here", "prefix": "{task_id_prefix}"}

    response = dict_value_substitutions(data=data, substitutions=substitutions)

    assert task_id in response.get("foo")
    assert response.get("prefix") == task_id.split("-")[0]
