from multiprocessing import Process
from time import sleep

import pytest
import requests
from path import Path

import tygs


def integration_app():
    app, http = tygs.webapp.WebApp.quickstart("namespace")

    @http.get('/')
    async def index(req, res):
        return res.template('index.html', {})

    @http.get('/get/<name>')
    async def get(req, res):  # not async, Tygs should make it awaitable
        return res.template('get.html', req.url_params)

    @http.post('/post')
    async def post(req, res):
        # import pdb
        # pdb.set_trace()
        return res.template('post.html', req.url_params)

    @http.put('/put')
    async def put(req, res):
        return res.template('index.html', req.url_params)

    @http.patch('/patch')
    async def patch(req, res):
        return res.template('index.html', req.url_params)

    @http.options('/options')
    async def options(req, res):
        return res.template('index.html', req.url_params)

    @http.head('/head')
    async def head(req, res):
        return res.template('index.html', req.url_params)

    @http.delete('/delete')
    async def delete(req, res):
        return res.template('index.html', req.url_params)

    @http.route('/mixed', ['GET', 'POST'])
    async def mixed(req, res):
        return res.template('index.html', {})

    return app, http


@pytest.yield_fixture(scope='module', autouse=True)
def start_server():
    def run(*args, **kwargs):  # noqa
        tygs.utils.aioloop()
        app, http = integration_app

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


def test_run_post(start_server):
    requests.post('http://localhost:8080/post', data={'key': 'value'})


def test_run_put(start_server):
    requests.put('http://localhost:8080/put', data={'key': 'value'})


def test_run_patch(start_server):
    requests.patch('http://localhost:8080/patch', data={'key': 'value'})


def test_run_options(start_server):
    requests.options('http://localhost:8080/options')


def test_run_head(start_server):
    requests.head('http://localhost:8080/head')


def test_run_delete(start_server):
    requests.delete('http://localhost:8080/delete')


def test_run_mixed(start_server):
    requests.get('http://localhost:8080/mixed')
    requests.post('http://localhost:8080/mixed')


def test_basic_xss(start_server):
    req = requests.get('http://localhost:8080/get/<h1>test')
    assert b'Hello, &lt;h1&gt;test!' == req.content
