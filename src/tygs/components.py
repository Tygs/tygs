import asyncio

import sys
import traceback

from functools import partial, wraps
from textwrap import dedent

import jinja2

from aiohttp.web_reqrep import Request
from aiohttp.web import RequestHandlerFactory, RequestHandler
import werkzeug

from .utils import ensure_coroutine, HTTP_VERBS
from .http.server import HttpRequestController, Router
from .exceptions import HttpResponseControllerError


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
        handler = ensure_coroutine(handler)
        self.signals.setdefault(event, []).append(handler)

    def trigger(self, event):
        handlers = self.signals.get(event, [])
        futures = (asyncio.ensure_future(handler()) for handler in handlers)
        gathering_future = asyncio.gather(*futures)

        # Ensure we drain any exception raised during our setup that
        # we didn't handle
        def on_main_future_done(fut):
            fut.exception()

        gathering_future.add_done_callback(on_main_future_done)

        return gathering_future

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

        try:
            template_name = response.context['template_name']

        except KeyError:
            raise HttpResponseControllerError(dedent("""
                    "{!r}" context doesn't contain a template name. When you
                    call res.template(), the template name is stored in
                    res.context['template_name']. Make sure nothing
                    overrides this key after it.
                  """.format(response)))

        body = self.render_to_string(template_name, response._renderer_data)
        body = body.encode(response.charset)

        return {'status': response.status_code,
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

        # Create shortcut methods for HTTP verbs
        for meth in HTTP_VERBS:
            setattr(self, meth.lower(), partial(self.route, methods=[meth]))

        # TODO: figure out namespace cascading from the app tree architecture

    # TODO: use explicit arguments
    def route(self, url, *args, methods=None, lazy_body=False, **kwargs):
        def decorator(func):

            func = ensure_coroutine(func)

            @wraps(func)
            async def handler_wrapper(req, res):
                if not lazy_body:
                    await req.load_body()
                return await func(req, res)

            # TODO: allow passing explicit endpoint
            endpoint = "{}.{}".format(self.app.ns, func.__name__)
            self.router.add_route(url, endpoint, handler_wrapper,
                                  methods=methods)
            return handler_wrapper
        return decorator

    def on_error(self, code, lazy_body=False):
        def decorator(func):

            func = ensure_coroutine(func)

            @wraps(func)
            async def handler_wrapper(req, res):

                if not lazy_body and req._aiohttp_request.has_body:
                    await req.load_body()
                return await func(req, res)

            # TODO: allow passing explicit endpoint
            self.router.add_error_handler(code, handler_wrapper)
            return handler_wrapper
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
        try:
            handler, arguments = await self._router.get_handler(tygs_request)
            tygs_request.url_args.update(arguments)
        except werkzeug.exceptions.HTTPException as e:
            handler = await self._router.get_error_handler(e.code)
            resp = tygs_request.response
            resp.status_code = e.code
            resp.reason = e.name
            resp.context['error_details'] = e.description

        tygs_request.handler = handler

        return tygs_request, handler

    async def _call_request_handler(self, req, handler):

        try:
            await handler(req, req.response)
        except Exception as e:
            # TODO: provide a debug web page and disable this
            # on prod
            handler = await self._router.get_error_handler(500)
            resp = req.response
            resp.status_code = 500
            resp.reason = 'Internal server error'

            tb = ''.join(traceback.format_exception(*sys.exc_info()))

            resp.context['error_details'] = tb
            # logging.error(e, exc_info=True)
            await handler(req, resp)

            # we still return the response because we have to (i.e. our tests
            # depends on an HTTP response)
            if self.tygs_app.fail_fast_mode:
                raise e

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
        await self._call_request_handler(tygs_request, handler)

        ###############

    # except HTTPException as exc:
    #     resp = exc

        response = tygs_request.response
        resp_msg = await self._write_response_to_client(tygs_request, response)

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
def aiohttp_request_handler_factory_adapter_factory(
        app, *, handler_adapter=AioHttpRequestHandlerAdapter):

    class AioHttpRequestHandlerFactoryAdapter(RequestHandlerFactory):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._handler = partial(handler_adapter, tygs_app=app)
            self._router = app.components['http'].router
            self._loop = asyncio.get_event_loop()
    return AioHttpRequestHandlerFactoryAdapter
