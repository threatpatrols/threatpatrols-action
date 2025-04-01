from threatpatrols_action.shared.lib import casts


def test_flatten_dict_01():
    x = {"foo": {"cat": "dog1"}, "bar": {"cat": "dog2"}, "sizzle": {"duck": {"cat": "dog3"}}}
    y = casts.flatten_dict(x, sep="-")

    assert y == {"foo-cat": "dog1", "bar-cat": "dog2", "sizzle-duck-cat": "dog3"}


def test_dict_to_flat_string_01():
    x = {"foo": "dog1", "bar": "dog2", "sizzle": "dog3"}
    y = casts.dict_to_flat_string(x)

    assert y == "foo='dog1' bar='dog2' sizzle='dog3'"


def test_list_to_dict_01():
    x = ["foo:hello world", "bar: 12345 ", "URL:https://www.google.com"]
    y = casts.list_to_dict(x)

    assert y == {"URL": "https://www.google.com", "bar": " 12345 ", "foo": "hello world"}


def test_str_to_numbers_01():
    x = "12345"
    y = casts.str_to_int(x)
    assert y == 12345

    x = "123.45999"
    y = casts.str_to_float(x)
    assert y == 123.45999
