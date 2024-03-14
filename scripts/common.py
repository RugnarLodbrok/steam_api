from pathlib import Path

from steam_api.client import client


def handle_empty_game_info(app_id):
    cache = client.get_app_info.cache.cache_backend
    if not cache[app_id]:
        f: Path = cache._key_file(app_id)
        if f.exists():
            f.unlink()
    else:
        raise AssertionError(app_id)
