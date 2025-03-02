import os
from uuid import uuid4

from hlid import HLID

from threatpatrols_action.shared.lib.substitutions import (
    dict_value_substitutions,
    list_value_substitutions,
    string_substitutions,
)


def test_substitutions01_basic():

    value = "hello {cruel} world"
    substitutions = {"cruel": "happy"}

    response = string_substitutions(value, substitutions)
    assert response == "hello happy world"


def test_substitutions02a_bad_token():

    value = "hello { cruel } world"  # << bad spaces around token
    substitutions = {"cruel": "happy"}

    response = string_substitutions(value, substitutions)
    assert "happy" not in response
    assert "{ cruel }" in response


def test_substitutions02b_bad_token():

    value = "hello { cruel } world"  # << bad spaces around token
    substitutions = {" cruel ": "happy"}

    response = string_substitutions(value, substitutions)
    assert "happy" not in response
    assert "{ cruel }" in response


def test_substitutions02c_not_exist():

    value = "hello {not_exist} world"
    substitutions = {"cruel": "happy"}

    response = string_substitutions(value, substitutions)
    assert "happy" not in response
    assert "{not_exist}" in response


def test_substitutions03a_double_token():

    task_id = str(HLID())
    call_id = str(HLID())

    value = "hello {task_id} world; another {call_id} here"
    substitutions = {"task_id": task_id, "call_id": call_id}

    response = string_substitutions(value, substitutions)
    assert response == f"hello {task_id} world; another {call_id} here"


# def test_substitutions03b_double_token():
#
#     task_id = str(HLID())
#     call_id = str(HLID())
#
#     value = "hello {task_id_prefix} world; another {call_id_prefix} here"
#     substitutions = {"task_id": task_id, "call_id": call_id}
#
#     task_id_prefix = task_id.split("-")[0]
#     call_id_prefix = call_id.split("-")[0]
#
#     response = string_substitutions(value, substitutions)
#     assert response == f"hello {task_id_prefix} world; another {call_id_prefix} here"


def test_substitutions04a_env():

    env_key = f"TEST_{str(uuid4().hex)[0:8].upper()}"
    env_value = str(HLID())
    os.environ[env_key] = env_value

    value = "hello ${" + env_key + "} world"

    response = string_substitutions(value)
    assert "$" not in response
    assert "{" not in response
    assert "}" not in response
    assert env_value in response


def test_substitutions04b_double_env():

    env_key1 = f"TEST_{str(uuid4().hex)[0:8].upper()}"
    env_value1 = str(HLID())
    os.environ[env_key1] = env_value1

    env_key2 = f"TEST_{str(uuid4().hex)[0:8].upper()}"
    env_value2 = str(HLID())
    os.environ[env_key2] = env_value2

    value = "this is the first ${" + env_key1 + "} env value; this is the second ${" + env_key2 + "} env value"

    response = string_substitutions(value)
    assert "$" not in response
    assert "{" not in response
    assert "}" not in response
    assert f"first {env_value1} env" in response
    assert f"second {env_value2} env" in response


def test_substitutions05_combined():

    task_id = str(HLID())
    another_task_id = str(HLID())

    env_value = str(HLID())
    os.environ["TEST_ENV_BEEP"] = env_value

    value = "hello {task_id} world; this has ${TEST_ENV_BEEP}  an extra space; and this is {another} thing"
    substitutions = {"task_id": task_id, "another": another_task_id}

    response = string_substitutions(value, substitutions)

    assert f"hello {task_id} world" in response
    assert f"this has {env_value}  an extra space" in response
    assert f"and this is {another_task_id} thing" in response


def test_substitutions06_dict():

    task_id = str(HLID())
    substitutions = {"task_id": task_id}
    data = {"foo": "this is {task_id} here", "prefix": "{task_id}"}

    response = dict_value_substitutions(data=data, substitutions=substitutions)

    assert task_id in response.get("foo")
    assert response.get("prefix") == task_id


def test_substitutions07_list():

    task_id = str(HLID())
    substitutions = {"task_id": task_id}
    data = ["this is {task_id} here", "{task_id}"]

    response = list_value_substitutions(data=data, substitutions=substitutions)

    assert response[0] == f"this is {task_id} here"
    assert response[1] == task_id
