import sys
import os
import asyncio
import inspect

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


def clean_exceptions_cb(fut):
    exc = fut.exception()
    if exc is not None:
        fut._loop.stop()
        raise exc


def exception_handler_factory(app):
    def exception_handler(loop, context):
        loop.default_exception_handler(loop, context)
        app.stop(context.get('exception'))
    return exception_handler
