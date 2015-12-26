import sys
import os

from path import Path


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {}

        cwd = Path(os.getcwd())
        # TODO: make this configurable
        self.project_dir = (cwd / sys.argv[0]).realpath().parent


    def ready():
        pass
