from tygs.utils import do_nothing

class TygsResponseError(object):
    pass

def html_renderer(response):
    """ Just send pure text.

        Only call write on request data.
    """
    response.headers['Content-Type'] = 'text/html'
    return response.data


def json_renderer(response):
    """ Send data as JSON.

        Set headers, serialize request data and write it.
    """
    response.headers['Content-Type'] = 'application/json'
    return json.dumps(response.data)


class TygsResponse(object):
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

    def html(self, data):
        if self.data:
            self.data += data
        else:
            self.data = data
        self.renderer = 'html'

    def json(self, data):
        if self.data:
            self.data.update(data)
        else:
            self.data = data
        self.renderer = 'json'

    def write(self, *args, **kwargs):
        # disable rendering then make write() a direct alias of request writting
        self.render = do_nothing
        self.html = self._no_rendering
        self.json = self._no_rendering
        self.write = self._req.write
        return self._req.write(*args, **kwargs)

    def _no_rendering(response):
        """ Raise an exception if you try to render.
        """
        error = "The response is already been sent, you can't render it now."
        TygsResponseError(error)


    def render(self):
        try:
            renderer = self.renderers[self.renderer]
        except KeyError:
            error = "Unknow response renderers '%s'" % self.renderer
            raise TygsResponseError(error)

        body = renderer(self)
        for key, val in self.headers.items():
            self._req.setHeader(key.encode('utf8'), val.encode('utf8'))

        self._req.write(body)
