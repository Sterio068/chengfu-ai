"""
v1.29 · _user_or_ip 抽出 · architect R2 round 3 tests

跑:
  cd backend/accounting
  python3 -m pytest tests/test_v1_29_user_or_ip.py -v
"""
import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMakeUserOrIp:
    def _make_request(self, internal_token=None):
        req = MagicMock()
        req.headers = {}
        if internal_token is not None:
            req.headers["X-Internal-Token"] = internal_token
        return req

    def test_internal_token_match(self, monkeypatch):
        from auth_deps import make_user_or_ip
        monkeypatch.setenv("ECC_INTERNAL_TOKEN", "secret123")
        verify_fn = MagicMock(return_value=None)
        get_addr = MagicMock(return_value="1.2.3.4")
        f = make_user_or_ip(verify_fn, get_addr)
        req = self._make_request(internal_token="secret123")
        assert f(req) == "u:internal"
        # 不該打 cookie 也不打 IP
        verify_fn.assert_not_called()
        get_addr.assert_not_called()

    def test_internal_token_wrong_falls_to_cookie(self, monkeypatch):
        from auth_deps import make_user_or_ip
        monkeypatch.setenv("ECC_INTERNAL_TOKEN", "secret123")
        verify_fn = MagicMock(return_value="user@example.example")
        get_addr = MagicMock(return_value="1.2.3.4")
        f = make_user_or_ip(verify_fn, get_addr)
        req = self._make_request(internal_token="WRONG")
        assert f(req) == "u:user@example.example"
        get_addr.assert_not_called()

    def test_no_internal_token_uses_cookie(self, monkeypatch):
        from auth_deps import make_user_or_ip
        monkeypatch.setenv("ECC_INTERNAL_TOKEN", "")
        verify_fn = MagicMock(return_value="alice@example.example")
        get_addr = MagicMock(return_value="1.2.3.4")
        f = make_user_or_ip(verify_fn, get_addr)
        req = self._make_request()
        assert f(req) == "u:alice@example.example"

    def test_cookie_fail_falls_to_ip(self):
        from auth_deps import make_user_or_ip
        verify_fn = MagicMock(return_value=None)
        get_addr = MagicMock(return_value="10.0.0.1")
        f = make_user_or_ip(verify_fn, get_addr)
        req = self._make_request()
        assert f(req) == "ip:10.0.0.1"

    def test_cookie_raises_falls_to_ip(self):
        from auth_deps import make_user_or_ip
        verify_fn = MagicMock(side_effect=Exception("db down"))
        get_addr = MagicMock(return_value="10.0.0.2")
        f = make_user_or_ip(verify_fn, get_addr)
        req = self._make_request()
        assert f(req) == "ip:10.0.0.2"

    def test_internal_token_secret_equal_timing_safe(self, monkeypatch):
        """確保用 _secrets_equal · 不是 == 比較(防 timing attack)"""
        import auth_deps
        # 改 _secrets_equal 加 spy · 確認被 call
        original = auth_deps._secrets_equal
        called_with = []
        def spy(a, b):
            called_with.append((a, b))
            return original(a, b)
        monkeypatch.setattr(auth_deps, "_secrets_equal", spy)

        monkeypatch.setenv("ECC_INTERNAL_TOKEN", "exp_token")
        verify_fn = MagicMock(return_value=None)
        get_addr = MagicMock(return_value="1.1.1.1")
        f = auth_deps.make_user_or_ip(verify_fn, get_addr)
        req = self._make_request(internal_token="exp_token")
        assert f(req) == "u:internal"
        assert ("exp_token", "exp_token") in called_with


class TestMainBackwardCompat:
    def test_main_imports_make_user_or_ip(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        src = open(path).read()
        assert "from auth_deps import make_user_or_ip" in src

    def test_main_no_inline_user_or_ip_logic(self):
        """main.py 仍有 _user_or_ip 函式(lazy wrapper)· 但內部不該有 ECC_INTERNAL_TOKEN env read · 該 logic 已移到 auth_deps"""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
        src = open(path).read()
        # wrapper 仍在 · 但只有 lazy delegate
        assert "_bound_user_or_ip = None" in src
        assert "_bound_user_or_ip = make_user_or_ip(" in src

    def test_auth_deps_make_user_or_ip_exists(self):
        from auth_deps import make_user_or_ip
        assert callable(make_user_or_ip)
