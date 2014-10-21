# coding: utf-8
#
# Copyright 2010 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Support for Bootle application style.

http://bottlepy.com

For more information see the bottle demo:
https://github.com/fiorix/cyclone/tree/master/demos/bottle
"""

from __future__ import absolute_import, unicode_literals, print_function

import cyclone.web
import sys

from twisted.python import log
from twisted.internet import reactor


class App(object):

    handlers = {}

    def route(self, path=None, method="any", **kwargs):

        def decorator(callback):
            name = method.lower()

            # Bottle lets users specify method="ANY" in order to catch any
            # route.
            name = 'default' if name == 'any' else name

            if path not in self.handlers:
                self.handlers[path] = Router()

            handler = self.handlers[path]
            handler.add(name, callback)

            return callback

        return decorator

    def run(self, **settings):
        port = settings.get("port", 8888)
        interface = settings.get("host", "0.0.0.0")
        log.startLogging(settings.pop("log", sys.stdout))
        reactor.listenTCP(port, cyclone.web.Application(self.handlers.items(),
                          **settings),
                          interface=interface)
        reactor.run()


class Router:
    def __init__(self):
        self.handler = type(b'CustomRequestHandler',
                            (cyclone.web.RequestHandler,), {})

    def add(self, method, callback):
        setattr(self.handler, method, callback)

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)
