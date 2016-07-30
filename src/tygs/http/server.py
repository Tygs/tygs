
import re
import asyncio

from textwrap import dedent

from aiohttp.web_reqrep import Response
from aiohttp.helpers import reify

from werkzeug.routing import Map, Rule

from tygs.exceptions import (HttpRequestControllerError,
                             HttpResponseControllerError,
                             RoutingError)
from tygs.utils import HTTP_VERBS, removable_property


# TODO: move this function and other renderers to a dedicated module
def text_renderer(response):
    body = response._renderer_data.encode(response.charset)

    return {'status': response.status,
            'reason': response.reason,
            'content_type': 'text/plain',
            'charset': response.charset,
            # TODO: update default heaers
            'headers': response.headers,
            'body': body
            }


# TODO: allow the user to configure a default renderer for when no renderer
# is set instead of getting this error. We'll need to update the exception
# message though
def no_renderer(response):
    raise HttpResponseControllerError(dedent("""
        No renderer set by the handler "{!r}" that received the request "{!r}".
        Please set manually a renderer or call one of the shortcut methods
        to do so (res.text(), res.template(), res.json(), etc).
    """.format(response.request.handler, response)))


class HttpRequestController:

    # TODO: decouple aiothttp_request from HttpRequestController
    # TODO: decouple httprequestcontroller from httprequest
    def __init__(self, app, aiohttp_request):
        self.app = app
        self._aiohttp_request = aiohttp_request

        self.server_name = aiohttp_request.host
        self.script_name = None  # TODO : figure out what script name does
        self.subdomain = None  # TODO: figure out subdomain handling
        self.method = aiohttp_request.method
        self.response = HttpResponseController(self)

        self.handler = None

        self.url_args = {}
        self.url_scheme = aiohttp_request.scheme
        self.url_path = aiohttp_request.path

    def __repr__(self):
        return "<{} {} {!r} >".format(self.__class__.__name__,
                                      self.method, self.url_path)

    # TODO: headers
    # TODO: cookies
    # TODO: raw data (query string, path, etc)

    def __getitem__(self, name):

        try:
            return self.url_query[name]
        except KeyError:
            pass

        try:
            return self.body[name]
        except HttpRequestControllerError as e:
            raise HttpRequestControllerError(dedent("""
                When you call HttpRequestController.__getitem__() (e.g: when
                you do req['something']), it implicitly tries to access
                HttpRequestController.body.

                If you see this error, it means you did it but you didn't call
                HttpRequestController.load_body() before, which is necessary
                to load and parse the request body.

                HttpRequestController.load_body is called automatically
                unless you used "lazy_body=True" in your routing code,
                so check it out.
                it out.
                """)) from e
        except KeyError as e:
            raise HttpRequestControllerError(dedent("""
                Item {!r} not found in the {!r} URL parameters nor the body.
                """.format(name, self))) from e

    def __iter__(self):
        for x in self.url_query:
            yield x
        for x in self.body:
            yield x

    def items(self):
        for x in self.url_query.items():
            yield x
        for x in self.body.items():
            yield x

    def values(self):
        for x in self.url_query.values():
            yield x
        for x in self.body.values():
            yield x

    def __contains__(self, name):
        return name in self.url_query or name in self.body

    def __len__(self):
        return len(self.url_query) + len(self.body)

    def __getattr__(self, name):

        verb = name.upper()
        if verb == "GET":
            raise HttpRequestControllerError(dedent("""
                There is no "GET" attribute. If you are looking for the
                data passed as the URL query sting (usually $_GET, .GET, etc.),
                use the "query_args" attribute.
            """))

        if verb in HTTP_VERBS:
            raise HttpRequestControllerError(dedent("""
                There is no "{0}" attribute. If you are looking for the
                request body (usually called $_POST, $_GET, etc.), use the
                "body" attribute. It works with all HTTP verbs and not
                just "{0}".
            """.format(name)))

        # Do not try super().__getattr__ since the parent doesn't define it.
        return object.__getattribute__(self, name)

    @reify
    def url_query(self):
        return self._aiohttp_request.GET

    @removable_property
    def body(self):
        raise HttpRequestControllerError(dedent("""
            You must await "HttpRequestController.load_body()" before accessing
            "HttpRequestController.body".

            This error can happen when you read "req.body" or
            "req['something']" (because it looks up in "req.body"
            after "req.query_args").

            "HttpRequestController.load_body()" is called automatically unless
            you used "lazy_body=True" in your routing code, so check it out.
        """))

    async def load_body(self):
        body = await self._aiohttp_request.post()
        self.body = body
        return body


# TODO: cookies
# TODO: send log info about multidict values: the user should know if she tries
# to access a single value from a multidict that has multiple values


class HttpResponseController:

    def __init__(self, request):
        self.request = request
        self._renderer = no_renderer
        self.template_engine = request.app.components.get('templates', None)
        self._renderer_data = None
        self.context = {"req": request, "res": self}

        # TODO : set reason automatically when you set status
        # TODO: create a status NameSpace with embeded reason and code
        self.status = 200
        self.content_type = "text/html"
        self.reason = "OK"
        self.charset = "utf-8"
        self.headers = {}

    def __repr__(self):
        req = self.request
        return "<{} {} {!r} >".format(self.__class__.__name__,
                                      req.method, req.url_path)

    def __getattr__(self, name):

        if name in ('status_code', 'code'):
            raise HttpResponseControllerError(dedent("""
                There is no "{0}" attribute. Use 'status'.
            """.format(name)))

        # Do not try super().__getattr__ since the parent doesn't define it.
        raise object.__getattribute__(self, name)

    # TODO: allow template engine to be passed here as a parameter, but
    # also be retrieved from the app configuration. And remove it as an
    # attribute of the HttpResponseController.
    def template(self, template, data=None):
        """
        Registers data variables and template name.
        This method does not actually render templates.
        """

        self.context['template_name'] = template

        self._renderer_data = {'context': self.context}
        self._renderer_data.update(data)

        # TODO make template engine pluggable
        self._renderer = self.template_engine.render_to_response_dict

        return self

    def text(self, message):
        self._renderer_data = str(message)
        self._renderer = text_renderer

    def render_response(self):
        return self._renderer(self)

    def _build_aiohttp_response(self):
        return Response(**self.render_response())


class Router:

    def __init__(self):
        self.url_map = Map()
        self.handlers = {}
        self.error_handlers = {
            "5**": self.default_error_handler,
            "4**": self.default_error_handler,
        }

    # TODO: remplace args and kwargs with explicit parameters
    # TODO: check if handler is a coroutine ?
    # TODO: remove a route
    def add_route(self, url, endpoint, handler, methods=None, *args, **kwargs):
        rule = Rule(url, endpoint=endpoint, methods=methods, *args, **kwargs)
        self.handlers[endpoint] = handler
        self.url_map.add(rule)

    async def get_handler(self, http_request):
        map_adapter = self.url_map.bind(
            server_name=http_request.server_name,
            script_name=http_request.script_name,
            subdomain=http_request.subdomain,
            url_scheme=http_request.url_scheme,
            default_method=http_request.method,
            path_info=http_request.url_path,
            query_args=http_request.url_query
        )

        # TODO:  MethodNotAllowed, RequestRedirect exceptions
        endpoint, arguments = map_adapter.match()
        return self.handlers[endpoint], arguments

    async def default_error_handler(self, req, res):
            return res.text(res.context['error_details'])

    def get_error_handler(self, code):

        code = str(code)
        try:
            return self.error_handlers[code]
        except KeyError:
            return self.error_handlers[code[0] + '**']

    # TODO: check if the status code exists in the HTTP spec and raise an
    # exception if it doesn't
    # TODO: check if handler is a coroutine ?
    # TODO: remove a handler
    def add_error_handler(self, code, handler):
        code = str(code)
        if not re.match(r'[45](\d\d|\*\*)', code):
            raise RoutingError(dedent("""
                The error code can only be a 400 or 500 HTTP status
                code either as the exact value (404, 503, etc) or
                in the form of a wild card (either 4** or 5**) to
                match all 400 or 500 errors. Other values (5*1,
                4444, 4xx, etc) are not allowed.
            """))

        self.error_handlers[code] = handler


class Server:

    def __init__(self, app):
        self.loop = asyncio.get_event_loop()
        self.app = app
        self.handler = self.app._aiohttp_app.make_handler()
        self._server_factory = self.loop.create_server(self.handler, '0.0.0.0',
                                                       8080)

    async def start(self):
        self.server = await asyncio.ensure_future(self._server_factory)
        self.app.register('stop', self.stop)

    async def stop(self):
        await self.handler.finish_connections(1.0)
        self.server.close()
        await self.server.wait_closed()
        await self.app._aiohttp_app.finish()
