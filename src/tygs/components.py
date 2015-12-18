class Component:

    def __init__(self):
        self.controllers = []


class Dispatcher:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.handlers = {}

    def dispatch(self, req):
        raise NotImplementedError()

# TODO: we may have to write abstractions of routers in order to get a unified
# interface
