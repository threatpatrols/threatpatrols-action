import os

from hlid import HLID

from threatpatrols_action.shared.lib.substitutions import (
    dict_value_substitutions,
    list_value_substitutions,
    string_substitutions,
)

task_id = str(HLID())
call_id = str(HLID())

substitutions = {
    "_tags": {"foo": "cat", "bar": 1, "other": [1, 2, 3, 4], "task_id": task_id, "call_id": call_id},
    "this": {"cruel": "happy"},
    "that": {"cruel": "unhappy"},
}


def test_substitutions01_basic_dict():
    value = "hello {tag.foo} world {this.cruel} other!"
    response = string_substitutions(value, substitutions)
    assert response == "hello cat world happy other!"


def test_substitutions02a_bad_token():
    value = "hello { this.cruel } world"  # << bad spaces around token
    response = string_substitutions(value, substitutions)
    assert "happy" not in response
    assert "{ this.cruel }" in response


def test_substitutions02b_not_exist():
    value = "hello {tag.foo.bar} world"
    response = string_substitutions(value, substitutions)
    assert response == "hello  world"


def test_substitutions03_double_token():
    value = "hello {tag.task_id} world; another {tag.call_id} here"
    response = string_substitutions(value, substitutions)
    assert response == f"hello {task_id} world; another {call_id} here"


def test_substitutions05_combined():
    env_value = str(HLID())
    os.environ["TEST_ENV_BEEP"] = env_value

    value = "hello {tag.task_id} world; this has ${TEST_ENV_BEEP}  an extra space; and this is {tag.bar} thing"
    response = string_substitutions(value, substitutions)

    assert f"hello {task_id} world" in response
    assert f"this has {env_value}  an extra space" in response
    assert "and this is 1 thing" in response


def test_substitutions06_dict():
    data = {"foo": "this is {tag.task_id} here", "other": "{tag.call_id}"}

    response = dict_value_substitutions(data=data, substitutions=substitutions)

    assert task_id in response.get("foo")
    assert response.get("other") == call_id


def test_substitutions07_list():
    data = ["this is {tag.task_id} here", "{tag.call_id}"]

    response = list_value_substitutions(data=data, substitutions=substitutions)

    assert response[0] == f"this is {task_id} here"
    assert response[1] == call_id
