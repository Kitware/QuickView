import asyncio
import inspect
from functools import wraps


def debounce(wait_time):
    """
    Decorator for debouncing functions in async code.
    """

    def decorator(fn):
        task = None

        @wraps(fn)
        def debounced(*args, **kwargs):
            nonlocal task

            # Cancel the pending execution task
            if task is not None:
                task.cancel()

            # Define an internal wrapper to handle the sleep and execution
            async def delayed_execution():
                await asyncio.sleep(wait_time)
                result = fn(*args, **kwargs)
                if inspect.isawaitable(result):
                    await result

            # Schedule the execution non-blockingly
            task = asyncio.create_task(delayed_execution())

        return debounced

    return decorator
