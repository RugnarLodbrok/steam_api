from time import sleep
from typing import Callable, ParamSpec, Type, TypeVar

T = TypeVar('T')
P = ParamSpec('P')
F = Callable[P, T]


def retry(
    exc_type: Type[Exception], n: int = 3, backoff_time: int = 0
) -> Callable[[F], F]:
    def decorator(f: F) -> F:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = exc_type
            for _ in range(n):
                try:
                    return f(*args, **kwargs)
                except exc_type as e:
                    last_exception = e
                    print(f'retry {exc_type}... {backoff_time} sec')
                    sleep(backoff_time)
            raise last_exception

        return wrapper

    return decorator
