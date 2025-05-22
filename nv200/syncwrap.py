"""
syncwrap.py

Utility module to convert asynchronous classes, functions, and entire modules
into synchronous interfaces using a shared background event loop.

Features:
- create_sync_class: Wraps async classes
- wrap_async_function: Wraps async functions
- wrap_async_module_functions: Replaces public async functions in a module
- create_sync_module: Builds a new module-like object with sync wrappers

Example usage:

    class AsyncAPI:
        async def fetch(self):
            await asyncio.sleep(1)
            return "data"

    SyncAPI = create_sync_class(AsyncAPI)
    api = SyncAPI()
    result = api.fetch()

    async def get_time():
        await asyncio.sleep(1)
        return time.time()

    sync_get_time = wrap_async_function(get_time)
    now = sync_get_time()

    import my_async_module
    sync_mod = create_sync_module(my_async_module)
    sync_mod.fetch_data()
"""

import asyncio
import threading
import atexit
import inspect
import types
from types import MethodType, ModuleType
from typing import Any, Callable, Coroutine, Optional, Type, TypeVar, Awaitable, cast

T = TypeVar("T")
R = TypeVar("R")


class AsyncSyncRunner:
    """
    Singleton background event loop runner to execute asyncio coroutines
    from synchronous code using a dedicated thread.
    """

    _instance: Optional["AsyncSyncRunner"] = None

    def __new__(cls) -> "AsyncSyncRunner":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
            atexit.register(cls._instance.stop)
        return cls._instance

    def _init(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)
        self.thread.start()

    def _start_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro: Coroutine[Any, Any, R]) -> R:
        """
        Run a coroutine on the background loop and block until the result is ready.

        Args:
            coro: The coroutine to execute.

        Returns:
            The result of the coroutine.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self) -> None:
        """
        Stop the background event loop and join the thread.
        Automatically called at program exit.
        """
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()
        type(self)._instance = None


_runner = AsyncSyncRunner()


def wrap_async_function(
    func: Callable[..., Awaitable[R]],
    preserve_name: bool = False
) -> Callable[..., R]:
    """
    Wrap a standalone async function to be callable synchronously.

    Args:
        func: The async function to wrap.
        preserve_name: If True, keeps the original function name. Otherwise, prefixes with 'sync_'.

    Returns:
        A synchronous function with the same signature.
    """
    def sync_func(*args: Any, **kwargs: Any) -> R:
        return _runner.run(func(*args, **kwargs))

    sync_func.__doc__ = f"Synchronous wrapper for async function `{func.__name__}`"
    sync_func.__name__ = func.__name__ if preserve_name else f"sync_{func.__name__}"
    return sync_func


def create_sync_class(async_cls: Type[T]) -> Type[T]:
    """
    Create a synchronous wrapper class around the given asynchronous class.

    Args:
        async_cls: The async class to wrap.

    Returns:
        A new class with the same interface, but coroutine methods are synchronous.
    """
    class SyncWrapper:
        def __init__(self, *args: Any, **kwargs: Any):
            self._async_instance = async_cls(*args, **kwargs)

            for attr_name in dir(self._async_instance):
                if attr_name.startswith("_"):
                    continue

                attr = getattr(self._async_instance, attr_name)

                if asyncio.iscoroutinefunction(attr):
                    sync_method = self._make_sync_method(attr)
                    setattr(self, attr_name, MethodType(sync_method, self))
                else:
                    setattr(self, attr_name, attr)

        def _make_sync_method(self, async_func: Callable[..., Coroutine[Any, Any, R]]) -> Callable[..., R]:
            def sync_func(this: Any, *args: Any, **kwargs: Any) -> R:
                return _runner.run(async_func(*args, **kwargs))
            return sync_func

        def close(self) -> None:
            """No-op for compatibility. Event loop is managed globally."""
            pass

        def __del__(self) -> None:
            """Avoid exceptions during garbage collection."""
            pass

    SyncWrapper.__name__ = f"Sync{async_cls.__name__}"
    return cast(Type[T], SyncWrapper)


def wrap_async_module_functions(module: ModuleType) -> None:
    """
    Replace all public top-level async functions in a module with sync equivalents (in-place).

    Args:
        module: The module object (already imported) to patch.
    """
    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if inspect.iscoroutinefunction(obj):
            wrapped = wrap_async_function(obj, preserve_name=True)
            setattr(module, name, wrapped)


def create_sync_module(module: ModuleType) -> types.SimpleNamespace:
    """
    Create a new module-like object with all public async functions
    from the original module wrapped to be synchronous.

    Args:
        module: The original async module (imported).

    Returns:
        A SimpleNamespace with the same public attributes,
        where async functions are replaced with sync wrappers.
    """
    sync_module = types.SimpleNamespace()

    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue

        if inspect.iscoroutinefunction(obj):
            wrapped = wrap_async_function(obj, preserve_name=True)
            setattr(sync_module, name, wrapped)
        else:
            setattr(sync_module, name, obj)

    return sync_module


_runner = None

def _init_runner() -> None:
    """
    Initialize the global event loop runner if it hasn't been created yet.

    If an event loop already exists for the current thread, it will be reused.
    Otherwise, a new event loop is created and set.
    """
    global _runner
    if _runner is None:
        try:
            _runner = asyncio.get_event_loop()
        except RuntimeError:
            _runner = asyncio.new_event_loop()
            asyncio.set_event_loop(_runner)


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    Run an async coroutine synchronously using a global event loop.

    Args:
        coro: The coroutine object to execute.

    Returns:
        The result of the coroutine once it has completed.

    Raises:
        Any exception raised during the coroutine's execution.
    """
    _init_runner()
    return _runner.run_until_complete(coro)