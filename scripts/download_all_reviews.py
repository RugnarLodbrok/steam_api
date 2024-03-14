from pathlib import Path

from scripts.common import handle_empty_game_info
from steam_api.client import NotFound, client
from steam_api.config import config


def check_stop() -> bool:
    stop_file = Path(__file__).parent / 'stop'
    if stop_file.exists():
        stop_file.unlink()
        return True
    return False


def download_reviews():
    games = client.get_player_owned_games(config.STEAM_MY_ID).games
    games = sorted(games, key=lambda game: -game.playtime_forever)
    for game in games[::-1]:
        try:
            app_info = client.get_app_info(game.id)
        except NotFound as e:
            print('NOT FOUND:', str(e))
            continue
        total_reviews = client.get_total_reviews(game.id)
        if not app_info:
            handle_empty_game_info(game.id)
            continue
        print(app_info.id, app_info.name or 'UNKNOWN', total_reviews)

        if game.id in client.get_reviews.cache.cache_backend:
            continue
        for i, r in enumerate(client.get_reviews(game.id), start=1):
            if not i % 10:
                print(f'\r{i}/{total_reviews}', end='')
        print('')
        if check_stop():
            break


if __name__ == '__main__':
    download_reviews()
