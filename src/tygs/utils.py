
import sys
import os
import asyncio
import inspect
import signal

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


# TODO: integrate this to signal dispatcher
class SigTermHandler:
    """ Allow to (un)register callbacks for when receiving SigTerm """

    all_signal_callbacks = set()
    _old_handler = None

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(*args, **kwargs)
        cls.install()
        return instance

    @classmethod
    def install(cls):
        if not cls._old_handler:
            cls._old_handler = signal.signal(signal.SIGTERM, cls.signal_wrapper)
            if callable(cls._old_handler):
                    cls.all_signal_callbacks.add(cls.old_handler)

    @classmethod
    def uninstall(cls):
        if cls._old_handler is not None:
            try:
                cls.all_signal_callbacks.remove(cls.old_handler)
            except KeyError:
                pass
        signal.signal(signal.SIGTERM, cls._old_handler)
        cls._old_handler = None

    def __init__(self):
        super(SigTermHandler, self).__init__()
        self.signal_callbacks = set()
        self.executed_exit_funcs = set()
        self._funcs_to_wrapper = {}

    def unregister_all_callbacks(self):
        """ Unregister all callbacks for this instance of SigTermHandler

            This does NOT affect callbacks from other instances of SigTermHandler
        """
        for callback in self.signal_callbacks:
            self.all_signal_callbacks.remove(callback)
        self.signal_callbacks.clear()

    def signal_wrapper(self, signum=None, frame=None):
        """ Send the signal again after our callbacks have all being called """
        for func in self.signal_callbacks:
            if func not in self.executed_exit_funcs:
                try:
                    func()
                finally:
                    self.executed_exit_funcs.add(func)
        # Only return the original signal this process was hit with
        # in case func returns with no errors, otherwise process will
        # return with sig 1.
        if signum is not None:
            if signum == signal.SIGINT:
                raise KeyboardInterrupt
            sys.exit(signum)

    def register(self, func):
        """Register a function which will be executed on "normal"
        interpreter exit or in case one of the `signal` is received
        by this process (differently from atexit.register()).

        Also, it makes sure to execute any previously registered
        via signal.signal(). If any, it will be executed after `func`.

        Functions which were already registered or executed via this
        function will be skipped.

        Exit function will not be executed on SIGKILL, SIGSTOP or
        os._exit(0).
        """

        if signal.getsignal(signal.SIGTERM) != self.signal_wrapper:
            raise RuntimeError("SigTermHandler has been used to set a callback "
                               "for SIGTERM but it has been overrided. Make "
                               "sure no other lib uses signal.signal directly "
                               "or call patch_signal()")

        # This further registration will be executed in case of clean
        # interpreter exit (no signal received).
        if func not in self.signal_callbacks:
            self.signal_callbacks.add(func)

    def patch_signal(self):
        self._old_signal = signal.signal
        signal.signal = self._signal_wrapper

    def un_patch_signal(self):
        signal.signal = self._old_signal

    def _signal_wrapper(self, signalnum, handler):
        """ Intercept signal registration for SIGTERM """
        if signalnum == signal.SIGTERM:
            return self.register_exit_func(handler)
        return signal.signal(signalnum, handler)

    def unregister(self, func):
        try:
            self.signal_callbacks.remove(func)
        except KeyError:
            pass


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
