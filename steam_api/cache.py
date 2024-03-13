from functools import cached_property
from inspect import isgeneratorfunction as is_generator
from pathlib import Path
from typing import Callable, Iterator, Literal, ParamSpec, Type, TypeVar

from pydantic import BaseModel

from steam_api.common import ROOT, AnyDict, AnyJson, identity
from steam_api.serializer import SerializerBase, SerializerYaml

T = TypeVar('T', bound=BaseModel)
P = ParamSpec('P')
F = Callable[P, T | None]


class CacheFiles:
    def __init__(self, path: Path, serializer: SerializerBase = SerializerYaml()):
        self._path = path
        self._no_args_mode: bool | None = None
        self._serializer = serializer

    @property
    def no_args_mode(self) -> bool:
        return self._no_args_mode  # pragma: no cover

    @cached_property
    def ext(self):
        return self._serializer.EXT

    @no_args_mode.setter
    def no_args_mode(self, value: bool) -> None:
        if value is False:
            self._path.mkdir(exist_ok=True, parents=True)
        elif value is True:
            self._path.parent.mkdir(exist_ok=True, parents=True)
        else:
            raise TypeError(value)  # pragma: no cover
        self._no_args_mode = value

    def _key_file(self, key: str) -> Path:
        if self._no_args_mode is False:
            return self._path / f'{key}.{self.ext}'
        if self._no_args_mode is True:
            return Path(f'{self._path}.{self.ext}')
        raise RuntimeError('mode is not set')  # pragma: no cover

    def __contains__(self, key: str) -> bool:
        return self._key_file(key).exists()

    def __getitem__(self, key: str) -> AnyJson:
        return self._serializer.load(self._key_file(key))

    def __setitem__(self, key: str, value: AnyJson) -> None:
        self._serializer.dump(self._key_file(key), value)

    def iter(self, key: str) -> Iterator[AnyJson]:
        return self._serializer.iter(self._key_file(key))

    def iter_write(self, key: str) -> Iterator[Callable[[AnyDict], None]]:
        return self._serializer.iter_write(self._key_file(key))


class CacheDecorator:
    def __init__(
        self,
        cache_backend: CacheFiles,
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

    def __call__(
        self,
        prefix: str,
        model: Type[BaseModel] | None = None,
        key: Literal['all_str', 'no_self', 'self_id'] | None = 'no_self',
        serializer: SerializerBase = SerializerYaml(),
    ) -> CacheDecorator:
        cache_backend = CacheFiles(path=self.path / prefix, serializer=serializer)
        return CacheDecorator(
            cache_backend, model, key_function=self.KEY_FUNCTIONS[key]
        )


cache = Cache(ROOT / 'cache')
