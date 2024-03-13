from pathlib import Path
from shutil import rmtree

import pytest

from steam_api.cache import Cache
from tests.utils import TestDatum


def allow_call_once(f):
    called = [False]

    def wrapper(*args, **kwargs):
        if called[0]:
            raise AssertionError('Called twice!')
        called[0] = True
        return f(*args, **kwargs)

    return wrapper


@pytest.fixture()
def func_one_arg():
    @allow_call_once
    def foo(arg: str):
        return TestDatum(name='a', arg=arg)

    return foo


@pytest.fixture
def cache_path() -> Path:
    return Path(__file__).parent / 'test_cache'


@pytest.fixture
def cacher(cache_path):
    yield Cache(cache_path)
    rmtree(cache_path)


def test_cache(cacher, func_one_arg, cache_path):
    cached_foo = cacher('subpath', key='all_str', model=TestDatum)(func_one_arg)
    cached_foo('ARG')
    result = cached_foo('ARG')
    assert result == TestDatum(name='a', arg='ARG')
    assert (cache_path / 'subpath' / 'arg.yml').read_text() == 'arg: ARG\nname: a\n'
