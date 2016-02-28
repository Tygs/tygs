
import asyncio

from functools import partial

import jinja2

from aiohttp.web_reqrep import Request
from aiohttp.web import RequestHandlerFactory, RequestHandler

from .utils import ensure_awaitable
from .http.server import HttpRequestController, Router


class Component:

    def __init__(self, app):
        self.app = app

    def setup(self):
        pass


class SignalDispatcher(Component):

    def __init__(self, app):
        super().__init__(app)
        self.signals = {}

    def register(self, event, handler):
        handler = ensure_awaitable(handler)
        self.signals.setdefault(event, []).append(handler)

    def trigger(self, event):
        handlers = self.signals.get(event, [])
        futures = (asyncio.ensure_future(handler) for handler in handlers)
        return asyncio.gather(*futures)

    def on(self, event):
        def decorator(func):
            self.register(event, func)
            return func
        return decorator


# TODO: make that a generic template renderer componnent
class Jinja2Renderer(Component):

    async def lazy_init(self):
        # TODO: make that configurable
        template_dir = self.app.project_dir / "templates"
        file_loader = jinja2.FileSystemLoader(template_dir)
        self.env = jinja2.Environment(loader=file_loader,
                                      autoescape=True)

    def setup(self):
        self.app.register('init', self.lazy_init)

    def render_to_string(self, template, context):
        # TODO : handle template not found
        template = self.env.get_template(template)
        return template.render(context)

    def render_to_response_dict(self, response):
        body = self.render_to_string(response.template, response.data)
        body = body.encode(response.charset)

        return {'status': response.status,
                'reason': response.reason,
                'content_type': response.content_type,
                'charset': response.charset,
                # TODO: update default heaers
                'headers': response.headers,
                'body': body
                }


class HttpComponent(Component):
    def __init__(self, app):
        super().__init__(app)
        self.router = Router()
        # TODO: figure out namespace cascading from the app tree architecture

    # TODO: use explicit arguments
    def get(self, url, *args, **kwargs):
        def decorator(func):
            # TODO: allow passing explicit endpoint
            endpoint = "{}.{}".format(self.app.ns, func.__name__)
            self.router.add_route(url, endpoint, func)
            return func
        return decorator


class AioHttpRequestHandlerAdapter(RequestHandler):

    def __init__(self, *args, tygs_app, **kwargs):
        super().__init__(*args, **kwargs)
        self.tygs_app = tygs_app

    async def _tygs_request_from_message(self, message, payload):
        app = self._app
        aiothttp_request = Request(
            app, message, payload,
            self.transport, self.reader, self.writer,
            secure_proxy_ssl_header=self._secure_proxy_ssl_header)

        # TODO: solve this issue with passing tygs app everywhere
        tygs_request = HttpRequestController(self.tygs_app, aiothttp_request)

        # for __repr__
        self._meth = aiothttp_request.method
        self._path = aiothttp_request.path

        return tygs_request

    async def _get_handler_and_tygs_req(self, message, payload):
        # message contains the HTTP headers, payload contains the request body
        tygs_request = await self._tygs_request_from_message(message, payload)
        handler, arguments = await self._router.get_handler(tygs_request)
        tygs_request.url_params.update(arguments)
        return tygs_request, handler

    async def handle_request(self, message, payload):
        if self.access_log:
            now = self._loop.time()

    # try:

        #############
        tygs_request, handler = await self._get_handler_and_tygs_req(message,
                                                                    payload)
        ############

        ####################
        # TODO: find out what do to with 100-continue message
        # expect = request.headers.get(hdrs.EXPECT)
        # if expect and expect.lower() == "100-continue":
        #     co = match_info.route.handle_expect_header(request)
        #     resp = await co
        # if resp is None:
        #    # TODO: add middlewares
        ############

        ###############
        await handler(tygs_request, tygs_request.response)
        ###############

    # except HTTPException as exc:
    #     resp = exc

        response = tygs_request.response
        resp_msg = self._write_response_to_client(tygs_request, response)

        # for repr
        self._meth = 'none'
        self._path = 'none'

        # log access
        if self.access_log:
            self.log_access(message, None, resp_msg, self._loop.time() - now)

    async def _write_response_to_client(self, request, response):
        aiohttp_reponse = response._build_aiohttp_response()
        resp_msg = await aiohttp_reponse.prepare(request._aiohttp_request)
        await aiohttp_reponse.write_eof()
        self.keep_alive(resp_msg.keep_alive())
        return resp_msg


# I'm so sorry
def aiohttp_request_handler_factory_adapter_factory(app):

    class AioHttpRequestHandlerFactoryAdapter(RequestHandlerFactory):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._handler = partial(AioHttpRequestHandlerAdapter, tygs_app=app)
            self._router = app.components['http'].router
            self._loop = asyncio.get_event_loop()
    return AioHttpRequestHandlerFactoryAdapter
