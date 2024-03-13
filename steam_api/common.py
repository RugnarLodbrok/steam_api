from pathlib import Path
from typing import Any, TypeVar

AnyDict = dict[str, Any]
_AnyJsonItem = AnyDict | bool | None
AnyJson = list[_AnyJsonItem] | _AnyJsonItem
ROOT = Path(__file__).parent.parent

T = TypeVar('T')


def identity(x: T) -> T:
    return x
