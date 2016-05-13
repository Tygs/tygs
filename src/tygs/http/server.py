
import asyncio

from aiohttp.web_reqrep import Response

from werkzeug.routing import Map, Rule


class HttpRequestController:

    # TODO: decouple aiothttp_request from HttpRequestController
    # TODO: decouple httprequestcontroller from httprequest
    def __init__(self, app, aiohttp_request):
        self.app = app
        self._aiohttp_request = aiohttp_request
        self.server_name = aiohttp_request.host
        self.script_name = None  # TODO : figure out what script name does
        self.subdomain = None  # TODO: figure out subdomain handling
        self.url_scheme = aiohttp_request.scheme
        self.method = aiohttp_request.method
        self.path_info = aiohttp_request.path
        self.query_args = aiohttp_request.query_string
        self.response = HttpResponseController(self)
        self.url_params = {}

# TODO: add aiohttp_request.POST and aiohttp_request.GET: remove multidict ?
# TODO: cookies


class HttpResponseController:

    def __init__(self, request):
        self.request = request
        self.renderer = None
        self.template_name = None
        self.template_engine = request.app.components.get('templates', None)
        self.data = {}
        # TODO : set reason automatically when you set status
        # TODO: create a status object with embeded reason
        self.status = 200
        self.content_type = "text/html"
        self.reason = "OK"
        self.charset = "utf-8"
        self.headers = {}

    def template(self, template, context=None):
        """
        Registers context variables and template name.
        This method does not actually render templates.
        """
        context = context or {}
        # TODO make template engine pluggable
        self.renderer = self.template_engine.render_to_response_dict
        self.template_name = template
        self.data.update(context)

        return self

    def render_response(self):
        return self.renderer(self)

    def _build_aiohttp_response(self):
        return Response(**self.render_response())


class Router:

    def __init__(self):
        self.url_map = Map()
        self.handlers = {}

    # TODO: remplace args and kwargs with explicit parameters
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
            path_info=http_request.path_info,
            query_args=http_request.query_args
        )

        # TODO: handle NotFound, MethodNotAllowed, RequestRedirect exceptions
        endpoint, arguments = map_adapter.match()
        return self.handlers[endpoint], arguments


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
