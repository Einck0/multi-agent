import functools
import logging
import time
from typing import Callable

from langgraph.types import Command

from graph.advanced_agent.state import State


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds to execute")
        return result

    return wrapper


def log_decorator(func: Callable) -> Callable:
    """Decorator to log function calls."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} returned: {result}")
        return result

    return wrapper


def retry_decorator(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry function calls on failure."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def update_previous_node(func: Callable) -> Callable:


    @functools.wraps(func)
    def wrapper(state: State, *args, **kwargs):
        # 获取当前函数名称
        current_node = func.__name__
        result = func(state, *args, **kwargs)
        if isinstance(result, Command):
            return result.update.update({'previous_node': current_node})
        elif "last_node" in result:
            return result.update({'previous_node': current_node})

        return result

    return wrapper

