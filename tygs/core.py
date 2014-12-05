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

"""Support for Bottle application style (see: http://bottlepy.com)

Depends on klein.
"""

from __future__ import absolute_import, unicode_literals, print_function

import inspect

from twisted.internet.defer import inlineCallbacks
from klein import Klein


from tygs.http import HTTPRequest, HTTPResponse


class App(object):

    def __init__(self):
        self.klein = Klein()

    def route(self, url, *args, **kwargs):
        """ Wrapper around Klein's routing to expose the Res/Req API to enpoints.

            Klein's routing assume an endpoint accepting only a request object
            and URL parameters. The new signature for endpoints is a request and
            a response objects and no params as they will be request attributes.
            This wrapper transforms the parameters into the new signature.
        """
        # Usual wrapper to create decorator with parameters.
        def decorator(func):
            f = func
            # This is the wrapper called for ALL endpoints. It create the
            # request and response objects and then call the end user
            # endpoint with these as parameters instead of only one request
            # object.
            def handle_request(request, *xargs, **xkwargs):
                req = HTTPRequest(request, *args, **kwargs)
                res = HTTPResponse(req)

                # if we see yield in the function, assume we want to inline
                # them as defer callbacks
                if inspect.isgeneratorfunction(f):
                    d =  inlineCallbacks(f)(req, res)
                    # TODO : better way to do this ?
                    d.addCallback(lambda x :res.render())
                    return d

                d =  f(req, res)
                res.render()

            handle_request.__name__ = b'handle_with__' + func.__name__

            # Bind the route to the handle_request endpoint which will call
            # the end user endpoint anyway.
            return self.klein.route(url, *args, **kwargs)(handle_request)

        return decorator

    def run(self):
        self.klein.run("localhost", 8080)
