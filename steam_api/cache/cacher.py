from inspect import isgeneratorfunction as is_generator
from pathlib import Path
from typing import Callable, Iterator, Literal, ParamSpec, Type, TypeVar

from pydantic import BaseModel

from steam_api.cache.backends import CacheBackend, CacheFiles
from steam_api.cache.serializers import SerializerBase, SerializerYaml
from steam_api.common import ROOT, AnyJson, identity

T = TypeVar('T', bound=BaseModel)
P = ParamSpec('P')
F = Callable[P, T | None]


class CacheDecorator:
    def __init__(
        self,
        cache_backend: CacheBackend,
        model: BaseModel | None,
        key_function: Callable[..., str] | None,
    ):
        self.cache_backend = cache_backend
        self.model = model
        self.key_function = key_function

    @staticmethod
    def _model_dump(data: BaseModel) -> AnyJson:
        return data and data.model_dump(by_alias=True, exclude_unset=True)

    def _model_load(self, data: AnyJson) -> BaseModel | None:
        return data and self.model.model_validate(data)

    def __call__(self, func: F) -> F:
        key_function = self.key_function
        self.cache_backend.no_args_mode = key_function is None
        if self.model:
            # todo: move to external middleware;
            #  both cache backend and serializers are middlewares too!
            _dump = self._model_dump
            _load = self._model_load
        else:
            _dump = identity
            _load = identity
        if not is_generator(func):

            def hit(key: str) -> T | None:
                result = self.cache_backend[key]
                return _load(result)

            def miss(key: str, result: T | None) -> T | None:
                self.cache_backend[key] = _dump(result)
                return result

        else:

            def hit(key: str) -> Iterator[T]:
                for item in self.cache_backend.iter(key):
                    yield _load(item)

            def miss(key: str, result: Iterator[T]) -> Iterator[T]:
                with self.cache_backend.iter_write(key) as feed:
                    for item in result:
                        feed(_dump(item))
                        yield item

        def wrapper(*args) -> T | None:
            key = key_function and key_function(*args)
            if key in self.cache_backend:
                return hit(key)
            return miss(key, func(*args))

        wrapper.cache = self
        return wrapper


class Cache:
    KEY_FUNCTIONS = {
        'all_str': lambda *args: '_'.join(str(arg) for arg in args),
        'no_self': lambda self, *args: '_'.join(str(arg) for arg in args),
        'self_id': lambda self: self.id,
        None: None,
    }

    def __init__(self, path: Path):
        self.path = path

    def __call__(  # pylint:disable=too-many-arguments
        self,
        prefix: str,
        model: Type[BaseModel] | None = None,
        key: Literal['all_str', 'no_self', 'self_id'] | None = 'no_self',
        serializer: SerializerBase = SerializerYaml(),
        cache_backend: Type[CacheBackend] = CacheFiles,
    ) -> CacheDecorator:
        return CacheDecorator(
            cache_backend(path=self.path / prefix, serializer=serializer),
            model,
            key_function=self.KEY_FUNCTIONS[key],
        )


cache = Cache(ROOT / 'cache')
