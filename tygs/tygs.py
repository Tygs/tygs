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


class TygsRequest(object):
    """ Proxy to the Twisted request object exposing the API to read the request.

        Most of the attributes are alias or wrapper arounds the underlying
        request object attributes. Some are added utility methods to make
        the end user life easier.
    """

    def __init__(self, werkzeug_request, *args, **kwargs):
        self.werkzeug_request = werkzeug_request
        self.url_args = args
        self.url_kwargs = kwargs


class TygsResponse(object):
    """ Proxy to the Twisted request object exposing the API to send a response.

        In the Twisted API, you build the response from the request object. We
        want to create facade to make the separation between request and
        response more obvious.

        Most of the attributes are alias or wrapper arounds the underlying
        request object attributes. Some are added utility methods to make
        the end user life easier.
    """

    def __init__(self, request):
        self.request = request
        self._req = self.request.werkzeug_request
        self.write = self._req.write


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

            # This is the wrapper called for ALL endpoints. It create the
            # request and response objects and then call the end user
            # endpoint with these as parameters instead of only one request
            # object.
            def handle_request(app, request, *xargs, **xkwargs):
                req = TygsRequest(request, *args, **kwargs)
                res = TygsResponse(req)

                # if we see yield in the function, assume we want to inline
                # them as defer callbacks
                if inspect.isgeneratorfunction(func):
                    return inlineCallbacks(func)(req, res)
                else:
                    return func(req, res)

            # Bind the route to the handle_request endpoint which will call
            # the end user endpoint anyway.
            return self.klein.route(url, *args, **kwargs)(handle_request)

        return decorator

    def run(self):
        self.klein.run("localhost", 8080)
