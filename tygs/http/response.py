# -*- coding: utf-8 -*-

"""
    Wrappers representing the HTTP response data and its rendering.
"""

from __future__ import absolute_import, unicode_literals

import json

from tygs.utils import do_nothing

class HTTPResponseError(object):
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
        self.renderer = 'html'
        self.data = None
        self.encoding = 'utf8'

    def html(self, data, encoding=None):
        """ Set next rendering of this response as HTML """
        if self.data:
            self.data += data
        else:
            self.data = data
        self.encoding = encoding or self.encoding
        self.renderer = 'html'

    def json(self, data, encoding=None):
        """ Set next rendering of this response as JSON """
        if self.data:
            self.data.update(data)
        else:
            self.data = data
        self.encoding = encoding or self.encoding
        self.renderer = 'json'

    def write(self, *args, **kwargs):
        """ Directly write data to the client.

            You probably don't want to use it directly, but if you do, you
            won't be able to use other rendering methods after it.
        """
        # disable rendering then make write() a direct alias of request writting
        self.render = do_nothing
        self.html = self._no_rendering
        self.json = self._no_rendering
        self.write = self._req.write
        return self._req.write(*args, **kwargs)

    def _no_rendering(response):
        """ Used to raise an exception if you try to render.
        """
        error = "The response is already been sent, you can't render it now."
        HTTPResponseError(error)


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
        for key, val in self.headers.items():
            self._req.setHeader(key.encode(self.encoding),
                                val.encode(self.encoding))

        self._req.write(body)
