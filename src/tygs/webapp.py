from . import App, components


class WebApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.components['http'] = components.HttpRouter()

    def ready(self):
        # TODO: start the aiohttp server, for now
        # TODO: implement
        # https://github.com/KeepSafe/aiohttp/blob/master/aiohttp/web_urldispatcher.py#L392
        pass

    @classmethod
    def quickstart(cls, ns):
        app = WebApp()
        return app, app.components['http']
