# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json

import pytest

from mock import MagicMock

from tygs.http import HTTPResponse, HTTPResponseError
from tygs.http.response import html_renderer, json_renderer
from tygs.utils import TygsEncodingError, do_nothing

from .test_request import request


@pytest.fixture
def response(request):
    return HTTPResponse(request)

def test_create_response(response, request):
    assert response.request == request
    assert response._req
    assert response.headers == {}
    assert response.renderer == 'html'
    assert response.data == ''
    assert response.encoding =='utf8'

def test_html(response):
    response.html('foo')
    assert response.data == 'foo'
    assert response.renderer == 'html'
    response.html('bar', encoding='cp1255')
    assert response.encoding == 'cp1255'
    assert response.data == 'foobar'
    response.html('bar', replace=True)
    assert response.data == 'bar'
    with pytest.raises(TygsEncodingError):
        response.html('bar', encoding='fjdksql')

def test_json(response):
    response.json({'foo': 'bar'})
    assert response.data == {'foo': 'bar'}
    assert response.renderer == 'json'
    response.json({'foo': 'bar'}, encoding='cp1255')
    assert response.encoding == 'cp1255'
    response.json({'bar': 'foo'})
    assert response.data == {'bar': 'foo', 'foo': 'bar'}
    response.json({'foo': 'bar'}, replace=True)
    assert response.data == {'foo': 'bar'}
    with pytest.raises(TygsEncodingError):
        response.json('bar', encoding='fjdksql')

def test_no_rendering(response):
    with pytest.raises(HTTPResponseError):
        response._no_rendering()

def test_encoding_property(response):
    response.encoding = 'cp1255'
    assert response.encoding == 'cp1255'
    with pytest.raises(TygsEncodingError):
        response.encoding = 'fdsqkfjqm'

def test_renderers(response):
    assert len(response.renderers) == 2
    assert response.renderers['html'] == html_renderer
    assert response.renderers['json'] == json_renderer
    response.renderer = 'json'
    with pytest.raises(HTTPResponseError):
        response.renderer = 'fdsqkfjqm'

def test_html_renderer(response):
    res = html_renderer(response)
    assert response.headers['Content-Type'] == 'text/html'
    assert res == b''
    response.data = 'é'
    response.encoding = 'cp850'
    res = html_renderer(response)
    assert res == 'é'.encode('cp850')

def test_json_renderer(response):
    res = json_renderer(response)
    assert response.headers['Content-Type'] == 'application/json'
    assert res == json.dumps('')
    response.data = {'é': 'é'}
    response.encoding = 'cp850'
    res = json_renderer(response)
    assert res == json.dumps({'é': 'é'}, encoding='cp850')

def test_disable_rendering(response):
    response._disable_rendering()
    assert response.render == do_nothing
    assert response.html == response._no_rendering
    assert response.json == response._no_rendering

def test_set_twisted_headers(response):
    response.headers['foo'] = 'bar'
    response._set_twisted_headers()
    response._req.setHeader.assert_called_once_with('foo', 'bar')

def test_write(response):
    assert response.write != response._req.write
    response._disable_rendering = MagicMock(name='_disable_rendering')
    response._set_twisted_headers = MagicMock(name='_set_twisted_headers')
    response.write(b'test')
    response._set_twisted_headers.assert_called_once_with()
    response._disable_rendering.assert_called_once_with()
    assert response.write == response._req.write
    response._req.write.assert_called_once_with(b'test')

def test_render(response):
    response.write = MagicMock(name='write')
    response.renderers['mock'] = MagicMock(return_value=b'test')
    response.renderer = 'mock'
    response.render()
    response.write.assert_called_once_with(b'test')
    response.renderers['mock'].assert_called_once_with(response)
