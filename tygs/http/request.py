# -*- coding: utf-8 -*-

"""
    Wrappers representing the HTTP request data and some helpers.
"""

from __future__ import absolute_import, unicode_literals

class HTTPRequest(object):
    """ Proxy to the Twisted request object exposing the API to read the request.

        Most of the attributes are alias or wrapper arounds the underlying
        request object attributes. Some are added utility methods to make
        the end user life easier.
    """

    def __init__(self, twisted_request, *args, **kwargs):
        self.twisted_request = twisted_request
        self.url_args = args
        self.url_kwargs = kwargs
