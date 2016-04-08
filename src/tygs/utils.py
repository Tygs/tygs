import sys
import os
import asyncio
import inspect

import contextlib

from path import Path


def get_project_dir():
    return (Path(os.getcwd()) / sys.argv[0]).realpath().parent


def ensure_awaitable(callable_obj):
    if not inspect.isawaitable(callable_obj):

        if not callable(callable_obj):
            raise TypeError("callable_obj must be an awaitable or a callable. "
                            "Did you try to call a non coroutine "
                            "by mistake?")

        # If a coroutine function is passed instead of a coroutine, call it
        # so everything is a coroutine.
        if inspect.iscoroutinefunction(callable_obj):
            callable_obj = callable_obj()

        # If a normal function is passed, wrap it as a coroutine.
        else:
            callable_obj = asyncio.coroutine(callable_obj)()

    return callable_obj


def aioloop():
    """ Ensure there is an opened event loop available and return it"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    policy.set_event_loop(loop)
    return loop


def aiorun(callable_obj):
    """ Run this in a event loop """
    loop = aioloop()
    awaitable = ensure_awaitable(callable_obj)
    return loop.run_until_complete(awaitable)


class DebugException(BaseException):

    old_factory = None
    fail_fast_mode = False

    def __init__(self, from_exception):
        self.from_exception = from_exception

    @classmethod
    def create_task_factory(cls, app):
        """
        Surcharge the default asyncio Task factory, by adding automatically an
        exception handler callback to every Task.
        Returning a factory instead of a Task prevents loop.get_task_factory()
        to be called for each Task.

        If you want to set up your own Task factory, make sure to call this one
        too, or you'll lose Tygs Task exceptions handling.
        """

        cls.fail_fast_mode = True
        loop = app.loop
        old_factory = loop.get_task_factory() or asyncio.Task

        def factory(loop, coro):
            task = old_factory(loop=loop, coro=coro)
            task.set_exception = app.break_loop_with_error
            return task

        return factory


@contextlib.contextmanager
def silence_loop_error_log(loop):
    old_handler = loop._exception_handler
    loop.set_exception_handler(lambda loop, context: None)
    yield
    loop.set_exception_handler(old_handler)
