
from aiohttp.web import Application

from .app import App

from .components import (HttpComponent,
                         aiohttp_request_handler_factory_adapter_factory,
                         Jinja2Renderer)

from .http.server import Server


class WebApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.components['http'] = HttpComponent(self)
        self.components['templates'] = Jinja2Renderer(self)
        self.http_server = None

        # aliasing this stupidly long name
        factory_adapter = aiohttp_request_handler_factory_adapter_factory
        self._aiohttp_app = Application(
            handler_factory=factory_adapter(self)
        )

    def ready(self, cwd=None):
        self.http_server = Server(self)
        self.register('ready', self.http_server.start)
        return super().ready(cwd)
        # TODO: start the aiohttp server, for now
        # TODO: implement
        # https://github.com/KeepSafe/aiohttp/blob/master/aiohttp/web_urldispatcher.py#L392

    async def async_ready(self, cwd=None):
        self.http_server = Server(self)
        self.register('ready', self.http_server.start)
        return super().async_ready(cwd)
        # TODO: start the aiohttp server, for now
        # TODO: implement
        # https://github.com/KeepSafe/aiohttp/blob/master/aiohttp/web_urldispatcher.py#L392

    @classmethod
    def quickstart(cls, ns):
        app = WebApp(ns)
        return app, app.components['http']
