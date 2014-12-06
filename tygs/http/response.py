# -*- coding: utf-8 -*-

"""
    Wrappers representing the HTTP response data and its rendering.
"""

from __future__ import absolute_import, unicode_literals

import json
import encodings

from tygs.utils import do_nothing, TygsError, raise_on_unsupported_encoding

class HTTPResponseError(TygsError):
    pass

def html_renderer(response):
    """ Just send pure text.

        Only call write on request data.
    """
    response.headers['Content-Type'] = 'text/html'
    return response.data.encode(response.encoding)


def json_renderer(response):
    """ Send data as JSON.

        Set headers, serialize request data and write it.
    """
    response.headers['Content-Type'] = 'application/json'
    return json.dumps(response.data, encoding=response.encoding)


class HTTPResponse(object):
    """ Proxy to the Twisted request object exposing the API to send a response.

        In the Twisted API, you build the response from the request object. We
        want to create facade to make the separation between request and
        response more obvious.

        Most of the attributes are alias or wrapper arounds the underlying
        request object attributes. Some are added utility methods to make
        the end user life easier.
    """

    renderers = {
        "html": html_renderer,
        "json": json_renderer,
    }

    def __init__(self, request):
        self.request = request
        self._req = self.request.twisted_request
        self.headers = {}
        self._renderer = 'html'
        self.data = ''
        self._encoding = 'utf8'

    @property
    def encoding(self):
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        raise_on_unsupported_encoding(value)
        self._encoding = value

    @property
    def renderer(self):
        return self._renderer

    @renderer.setter
    def renderer(self, value):
        if value not in self.renderers:
            msg = ("'%s' is not a supported encoding. "
                   "Check 'self.renderers' for supported renderers.")
            raise HTTPResponseError(msg % value)
        self._renderer = value


    def html(self, data, encoding=None, replace=False):
        """ Set next rendering of this response as HTML

            If previous data existed in the response, and replace is False,
            an attempt to merge the new data with it by concatenation will be
            made before falling back on replacement.
        """
        # Todo : check that data is a unicode string. We'll need future
        if data and not replace:
            try:
                self.data += data
            except TypeError:
                self.data = data
        else:
            self.data = data
        self.encoding = encoding or self.encoding
        self.renderer = 'html'

    def json(self, data, encoding=None, replace=False):
        """ Set next rendering of this response as JSON

            If previous data existed in the response, and replace is False,
            an attempt to merge the new data with it by update() will be
            made before falling back on replacement.
        """
        if data and not replace:
            try:
                self.data.update(data)
            except (AttributeError, ValueError):
                self.data = data
        else:
            self.data = data
        self.encoding = encoding or self.encoding
        self.renderer = 'json'

    def _disable_rendering(self):
        """ Disable rendering then make write() an alias of request writting """
        self.render = do_nothing
        self.html = self._no_rendering
        self.json = self._no_rendering

    def _set_twisted_headers(self):
        """ Copy the headers to the twisted request object """
        for key, val in self.headers.items():
            self._req.setHeader(key.encode(self.encoding),
                                val.encode(self.encoding))

    def write(self, *args, **kwargs):
        """ Directly write data to the client.

            You probably don't want to use it directly, but if you do, you
            won't be able to use other rendering methods after it.
        """
        self._disable_rendering()
        self._set_twisted_headers()
        res = self._req.write(*args, **kwargs)
        # if we call write again, it will do a direct write to the client
        self.write = self._req.write
        return res

    def _no_rendering(response):
        """ Used to raise an exception if you try to render.
        """
        error = "The response is already been sent, you can't render it now."
        raise HTTPResponseError(error)


    def render(self):
        """ Applies the proper renderer to the response and write the result.

            Get the proper callable from the renderer mapping and applies it.
            Then, write back the response to the client, headers included.
        """
        try:
            renderer = self.renderers[self.renderer]
        except KeyError:
            error = "Unknow response renderers '%s'" % self.renderer
            raise HTTPResponseError(error)
        body = renderer(self)
        self.write(body)
