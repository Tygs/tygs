
from aiohttp.web import Application

from .app import App
from .http.server import Server
from .components import (HttpComponent,
                         aiohttp_request_handler_factory_adapter_factory,
                         Jinja2Renderer)


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
        super().ready(cwd)
        self.http_server = Server(self)
        self.http_server.run()
        # TODO: start the aiohttp server, for now
        # TODO: implement
        # https://github.com/KeepSafe/aiohttp/blob/master/aiohttp/web_urldispatcher.py#L392
        pass

    @classmethod
    def quickstart(cls, ns):
        app = WebApp(ns)
        return app, app.components['http']
