
import tygs

from .components import SignalDispatcher


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher()}
        self.project_dir = None

    def on(self, event):
        return self.components['signals'].on(event)

    def trigger(self, event):
        return self.components['signals'].trigger(event)

    def ready(self, cwd=None):
        if cwd is None:
            cwd = tygs.utils.get_project_dir()
        self.project_dir = cwd
        self.trigger('ready')
