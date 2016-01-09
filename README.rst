Tygs
====

Tygs wants to be a Pure Python Web framework providing a sweet API for :

- easy asynchronous HTTP;
- PUB/SUB between your code on: server/server, server-client, client-client;
- RPC between your code on: server/server, server-client, client-client;
- easy task queues;
- in memory key/value store for caching and more;
- multiprocessing to bypass the GIL and still play nice and easy with the above.

For now it's nothing, since the project just started. No promises.

Depandancies:

- Python 3.5+ (uses async/await);
- aiohttp
- jinja2
- aiohttp-jinja2,
- path.py

Licence: WTFPL

Install
--------

It is not pushed on pypi yet::

    python setup.py install

Developement
-------------

Install for dev::

    python setup.py develop

Style Guide :
 - Python: PEP8 (https://www.python.org/dev/peps/pep-0008/)
 - JS: Google (http://google-styleguide.googlecode.com/svn/trunk/javascriptguide.xml)

Deactivate dev mode:

    python setup.py develop --uninstall

Running all tests::

    python setup.py test

This can take long has it will setup the whole test env with tox, a virtualenv, etc.

You can install test dependancies manually::

    pip install pytest-cov, mock, tox

And run the tests manually::

    # in all envs
    tox
    # in only the current env
    py.test tests

After that, you can run tests covergage this way::

    # cmd only coverage
    py.test --cov tygs tests
    # dump an HTML report in htmlcov dir
    py.test  --cov-report html --cov tygs tests
