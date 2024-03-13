import abc
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

import yaml

from steam_api.common import AnyDict, AnyJson


class SerializerBase:
    @property
    @abc.abstractmethod
    def EXT(self) -> str:  # pylint:disable=invalid-name
        ...

    @abc.abstractmethod
    def dump(self, path: Path, data: AnyJson) -> None:
        ...

    @abc.abstractmethod
    def load(self, path: Path) -> AnyJson:
        ...

    def iter(self, path) -> Iterator[AnyJson]:
        raise NotImplementedError

    def iter_write(self, path) -> Iterator[Callable[[AnyDict], None]]:
        raise NotImplementedError


class SerializerJson(SerializerBase):
    EXT = 'json'

    def dump(self, path: Path, data: AnyJson) -> None:
        with open(path, 'wt') as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path: Path) -> AnyJson:
        with open(path, 'rt') as f:
            return json.load(f)


class SerializerYaml(SerializerBase):
    EXT = 'yml'

    def dump(self, path: Path, data: AnyJson) -> None:
        with open(path, 'wt') as f:
            yaml.dump(data, stream=f, allow_unicode=True)

    def load(self, path: Path) -> AnyJson:
        with open(path, 'rt') as f:
            return yaml.load(f, yaml.SafeLoader)

    def iter(self, path) -> Iterator[AnyJson]:
        for chunk in self._yaml_chunks(path):
            yield yaml.load(chunk, yaml.SafeLoader)[0]

    @contextmanager
    def iter_write(self, path: Path) -> Iterator[Callable[[AnyDict], None]]:
        with open(path, 'wt') as f:

            def feed(item: AnyDict):
                f.write(yaml.dump([item], allow_unicode=True))

            yield feed

    @staticmethod
    def _yaml_chunks(path: Path) -> Iterator[str]:
        chunk = ''
        with open(path, 'rt') as f:
            for line in f:
                if not chunk:
                    assert line.startswith('- ')
                    chunk = line
                elif line.startswith('- '):
                    yield chunk
                    chunk = line
                else:
                    chunk += line
            if chunk:
                yield chunk
