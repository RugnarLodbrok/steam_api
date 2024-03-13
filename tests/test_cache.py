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


@pytest.fixture()
def cached_method(cacher):
    class A:
        def __init__(self):
            self.counter = 0

        @cacher('prefix', key='no_self', model=None)
        def foo(self, arg1, arg2):
            self.counter += 1
            return TestDatum(name=str(self.counter), arg=f'{arg1}@{arg2}').model_dump()

    return A().foo


@pytest.fixture
def cache_path() -> Path:
    return Path(__file__).parent / 'test_cache'


@pytest.fixture
def cacher(cache_path):
    yield Cache(cache_path)
    rmtree(cache_path)


def test_cache(cacher, func_one_arg, cache_path):
    cached_foo = cacher('prefix', key='all_str', model=TestDatum)(func_one_arg)
    cached_foo('ARG')
    result = cached_foo('ARG')
    assert result == TestDatum(name='a', arg='ARG')
    assert (cache_path / 'prefix' / 'arg.yml').read_text() == 'arg: ARG\nname: a\n'


def test_cache_singleton(func_no_args, cacher, cache_path):
    cached_foo = cacher('prefix', key=None, model=TestDatum)(func_no_args)
    cached_foo()
    result = cached_foo()
    assert result == TestDatum(name='a')
    assert (cache_path / 'prefix.yml').read_text() == 'name: a\n'


def test_cache_method(cached_method, cache_path):
    cached_method('a', 'b')
    cached_method('a', 'c')
    result = cached_method('a', 'c')
    assert result == {'arg': 'a@c', 'name': '2'}
    assert (cache_path / 'prefix' / 'a_b.yml').read_text() == "arg: a@b\nname: '1'\n"
    assert (cache_path / 'prefix' / 'a_c.yml').read_text() == "arg: a@c\nname: '2'\n"
