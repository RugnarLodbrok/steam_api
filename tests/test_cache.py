from pathlib import Path
from shutil import rmtree

import pytest

from steam_api.cache import Cache
from tests.utils import TestDatum


@pytest.fixture()
def func_one_arg():
    counter = [0]

    def foo(arg: str):
        name = 'a'
        if counter[0]:
            name = str(counter[0])
        counter[0] += 1
        return TestDatum(name=name, arg=arg)

    return foo


@pytest.fixture()
def func_no_args():
    counter = [0]

    def foo():
        name = 'a'
        if counter[0]:
            name = str(counter[0])
        counter[0] += 1
        return TestDatum(name=name)

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


def test_cache_singleton(func_no_args, cacher, cache_path):
    cached_foo = cacher('subpath', key=None, model=TestDatum)(func_no_args)
    cached_foo()
    result = cached_foo()
    assert result == TestDatum(name='a')
    assert (cache_path / 'subpath.yml').read_text() == 'name: a\n'
