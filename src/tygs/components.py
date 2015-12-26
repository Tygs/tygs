
from functools import partial

import jinja2
import asyncio

from aiohttp.abc import AbstractRouter, AbstractMatchInfo
from aiohttp.web_urldispatcher import Route
from aiohttp.web_reqrep import Request
from aiohttp.web import RequestHandlerFactory, RequestHandler
from aiohttp.web_exceptions import HTTPException

from .http.server import HttpRequest, Router


class Component:

    def __init__(self, app):
        self.app = app


# TODO: make that a generic template renderer componnent
class Jinja2Renderer(Component):

    def __init__(self, app):
        super().__init__(app)
        # TODO: make that configuratble
        template_dir = app.project_dir / "templates"
        file_loader = jinja2.FileSystemLoader(template_dir)
        self.env = jinja2.Environment(loader=file_loader)

    def render(self, template, context):
        # TODO : handle template not found
        template = self.env.get_template(template)
        return template.render(context)



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
        return decorator


class AioHttpRequestHandlerAdapter(RequestHandler):


    def __init__(self, *args, tygs_app, **kwargs):
        super().__init__(*args, **kwargs)
        self.tygs_app = tygs_app


    async def handle_request(self, message, payload):
        if self.access_log:
            now = self._loop.time()

        app = self._app
        aiothttp_request = Request(
            app, message, payload,
            self.transport, self.reader, self.writer,
            secure_proxy_ssl_header=self._secure_proxy_ssl_header)

        # TODO: solve this issue with passing tygs app everywhere
        tygs_request = HttpRequest(self.tygs_app, aiothttp_request)

        # for __repr__
        self._meth = aiothttp_request.method
        self._path = aiothttp_request.path

        try:

            #############
            handler, arguments = await self._router.get_handler(tygs_request)
            tygs_request.url_params.update(arguments)
            ############

            ####################
            # TODO: find out what do to with 100-continue message
            # expect = request.headers.get(hdrs.EXPECT)
            # if expect and expect.lower() == "100-continue":
            #     resp = (
            #         yield from match_info.route.handle_expect_header(request))
            # if resp is None:
            #    # TODO: add middlewares
            ############

            ###############

            await handler(tygs_request, tygs_request.response)

            ###############

        except HTTPException as exc:
            resp = exc

        aiohttp_reponse = tygs_request.response._build_aiohttp_reponse()
        resp_msg = await aiohttp_reponse.prepare(aiothttp_request)
        await aiohttp_reponse.write_eof()

        # notify server about keep-alive
        self.keep_alive(resp_msg.keep_alive())

        # log access
        if self.access_log:
            self.log_access(message, None, resp_msg, self._loop.time() - now)

        # for repr
        self._meth = 'none'
        self._path = 'none'


# I'm so sorry
def aiohttp_request_handler_factory_adapter_factory(app):

    class AioHttpRequestHandlerFactoryAdapter(RequestHandlerFactory):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._handler = partial(AioHttpRequestHandlerAdapter, tygs_app=app)
            self._router = app.components['http'].router
    return AioHttpRequestHandlerFactoryAdapter
