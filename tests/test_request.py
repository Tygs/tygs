# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytest

from mock import Mock

from tygs.http import HTTPRequest

@pytest.fixture
def request():
    return HTTPRequest(Mock(), 1, 2, foo='bar')


def test_request(request):
    assert request.twisted_request
    assert request.url_args == (1, 2)
    assert request.url_kwargs == {'foo': 'bar'}