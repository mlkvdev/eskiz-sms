import pytest

from eskiz_sms import exceptions, types
from . import config


class TestClass:

    def test_invalid_token(self):
        eskiz = config.get_eskiz_instance(False, False)
        eskiz.token.set(config.ESKIZ_INVALID_TOKEN)
        with pytest.raises(exceptions.BadRequest):
            eskiz.get_limit()

    def test_expired_token(self):
        eskiz = config.get_eskiz_instance(False, False)
        eskiz.token.set(config.ESKIZ_EXPIRED_TOKEN)
        with pytest.raises(exceptions.TokenExpiredException):
            eskiz.get_limit()

    def test_valid_token(self):
        eskiz = config.get_eskiz_instance(False, False)
        eskiz.token.set(config.ESKIZ_TOKEN)
        response = eskiz.get_limit()
        assert type(response) is types.Response

    def test_auto_update(self):
        eskiz = config.get_eskiz_instance(False, True)
        eskiz.token.set(None)
        response = eskiz.get_limit()
        assert type(response) is types.Response

    def test_without_auto_update(self):
        eskiz = config.get_eskiz_instance(False, False)
        eskiz.token.set(None)
        response = eskiz.get_limit()
        assert type(response) is types.Response

    def test_saving_token(self):
        eskiz = config.get_eskiz_instance(True, False)
        eskiz.token.set(None)
        response = eskiz.get_limit()
        assert type(response) is types.Response
