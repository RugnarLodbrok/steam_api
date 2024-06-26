import abc
from functools import cached_property
from pathlib import Path
from typing import Callable, Iterator

from steam_api.cache.serializers import SerializerBase
from steam_api.common import AnyDict, AnyJson


class CacheBackend:
    def __init__(self, path: Path, serializer: SerializerBase):
        self._path = path
        self._no_args_mode: bool | None = None
        self._serializer = serializer

    @cached_property
    def ext(self):
        return self._serializer.EXT

    @property
    def no_args_mode(self) -> bool:
        return self._no_args_mode  # pragma: no cover

    @no_args_mode.setter
    def no_args_mode(self, value: bool) -> None:
        if value is False:
            self._path.mkdir(exist_ok=True, parents=True)
        elif value is True:
            self._path.parent.mkdir(exist_ok=True, parents=True)
        else:
            raise TypeError(value)  # pragma: no cover
        self._no_args_mode = value

    @abc.abstractmethod
    def __contains__(self, key: str) -> bool:
        ...

    @abc.abstractmethod
    def __getitem__(self, key: str) -> AnyJson:
        ...

    @abc.abstractmethod
    def __setitem__(self, key: str, value: AnyJson) -> None:
        ...


class CacheOneFile(CacheBackend):
    def __init__(self, path: Path, serializer: SerializerBase):
        super().__init__(path, serializer)
        self._data: AnyDict | None = None
        self._file = self._path.with_suffix('.' + self.ext)

    @property
    def data(self) -> AnyDict:
        if self._data is None:
            if self._file.exists():
                self._data = self._serializer.load(self._file)
            else:
                self._file.parent.mkdir(exist_ok=True, parents=True)
                self._data = {}

        return self._data

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def __getitem__(self, key: str) -> AnyJson:
        return self.data[key]

    def __setitem__(self, key: str, value: AnyJson) -> None:
        self.data[key] = value
        self._serializer.dump(self._file, self.data)


class CacheFiles(CacheBackend):
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
