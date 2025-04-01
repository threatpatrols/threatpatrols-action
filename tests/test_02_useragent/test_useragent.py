from threatpatrols_action.shared.lib.user_agent import UserAgent


def test_find():
    user_agent = UserAgent().find("Windows NT", "x64", "Chrome/")
    assert "Chrome" in user_agent


def test_find_desktop():
    user_agent = UserAgent(family="desktop").find("Windows NT", "x64", "Chrome/")
    assert "Chrome" in user_agent


def test_find_mobile():
    # "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
    user_agent = UserAgent(family="mobile").find("iPhone")

    assert "Safari" in user_agent
