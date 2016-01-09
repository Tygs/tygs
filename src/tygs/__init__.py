
"""
    Main entry point for tygs, an experimental modern Python Web framework.

    Tygs wants to be a Pure Python Web framework providing a sweet API for :

     - easy asynchronous HTTP;
     - PUB/SUB between your code on: server/server, server-client,
         client-client;
     - RPC between your code on: server/server, server-client, client-client;
     - easy task queues;
     - in memory key/value store for caching and more;
     - multiprocessing to bypass the GIL and still
         play nice and easy with the above.

    For now it's nothing, since the project just started. No promises.

    Depandancies:

        Python 3.5+ (uses async/await);
        aiohttp
        jinja2
        aiohttp-jinja2,
        path.py

    Licence: WTFPL

    Learn more at https://github.com/Tygs/tygs.

"""

from .webapp import WebApp  # noqa
