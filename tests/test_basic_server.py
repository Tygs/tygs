from multiprocessing import Process
from time import sleep

import pytest
import requests
from path import Path

import tygs


@pytest.yield_fixture(scope='module', autouse=True)
def start_server():
    def run(*args, **kwargs):  # noqa
        tygs.utils.aioloop()
        app, http = tygs.webapp.WebApp.quickstart("namespace")

        @http.get('/')
        async def index(req, res):
            return res.template('index.html', {})

        @http.get('/get/<name>')
        async def get(req, res):  # not async, Tygs should make it awaitable
            return res.template('get.html', req.url_params)

        @http.post('/post')
        async def post(req, res):
            return res.template('post.html', req.url_params)

        app.ready(*args, **kwargs)

    path = Path(__file__).parent / 'fixtures'
    t = Process(target=run, kwargs={'cwd': path})
    t.start()
    sleep(1)
    yield
    t.terminate()
    t.join()


def test_run_index(start_server):
    req = requests.get('http://localhost:8080')
    assert b'Hello, world!' == req.content

    req = requests.get('http://localhost:8080/get/tygs')
    assert b'Hello, tygs!' == req.content


def test_basic_xss(start_server):
    req = requests.get('http://localhost:8080/get/<h1>test')
    assert b'Hello, &lt;h1&gt;test!' == req.content
