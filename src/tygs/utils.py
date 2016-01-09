
import sys
import os

from path import Path

def get_project_dir():
    return (Path(os.getcwd()) / sys.argv[0]).realpath().parent