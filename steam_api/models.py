from functools import cached_property
from pathlib import Path
from typing import Iterator, Self

import yaml
from pydantic import BaseModel

from steam_api.cache import cache
from steam_api.client import NotFound, client
from steam_api.common import ROOT
from steam_api.config import config
from steam_api.schemas import App, OwnedGame, Review, ReviewsSummary


class MyRate(BaseModel):
    annotation: dict[str, str]
    games: dict[str, str | None]
    path: str

    @classmethod
    def load(cls, path: Path = ROOT / 'data' / 'my_rate.yml') -> Self:
        json = yaml.safe_load(path.read_text())
        json['path'] = str(path)
        return cls.parse_obj(json)

    def save(self):
        with open(self.path, 'wt') as f:
            yaml.dump(self.dict(exclude={'path'}), f, allow_unicode=True)


class Game:
    def __init__(self, owned_game: OwnedGame | None = None, app_id: int | None = None):
        self._owned_game = owned_game
        if owned_game:
            self.id = owned_game.id
        elif app_id:
            self.id = app_id
        else:
            raise ValueError('one of `owned_game` or `app_id` are expected')
        self._app: App | None = None
        self._review_summary: ReviewsSummary | None = None

    @property
    def app_info(self) -> App | NotFound:
        if not self._app:
            try:
                self._app = client.get_app_info(self.id)
            except NotFound:
                self._app = NotFound
        return self._app

    @property
    def review_summary(self) -> ReviewsSummary:
        if not self._review_summary:
            self._review_summary = client.get_review_summary(self.id)
        return self._review_summary

    @classmethod
    def from_name(cls, name: str):
        return cls(app_id=app_name_map[name])

    @property
    def total_played(self) -> int:
        return self.owned_game.playtime_forever

    @cached_property
    def name(self) -> str:
        if self.app_info is NotFound:
            return 'NOT FOUND'
        return self.app_info.name.strip()

    @property
    def total_reviews(self) -> int:
        return self.review_summary.total_reviews

    @classmethod
    def users_games(cls, steam_id: int):
        owned_games = client.get_player_owned_games(steam_id).games
        return [cls(game) for game in owned_games]

    @property
    def reviews(self) -> Iterator[Review]:
        return client.get_reviews(self.id)


class AppNameMap:
    def __init__(self, correction_file: Path) -> None:
        self._map = {}
        self._correction_file = correction_file

    def __getitem__(self, item: str) -> int:
        return self.map[item]

    @property
    def map_(self):
        if not self._map:
            all_apps = client.get_all_apps()
            _map = self._map
            for item in all_apps:
                app_id = item['appid']
                name = item['name']
                _map[name] = app_id
            correction = yaml.safe_load(self._correction_file.read_text())
            _map.update(correction)
        return self._map

    @property
    @cache('game_name_id_map', model=None, key=None)
    def map(self):
        map_ = {}
        for game in Game.users_games(config.STEAM_MY_ID):
            if game.name == 'NOT FOUND':
                continue
            map_[game.name] = game.id
        return map_

    @cached_property
    def metrics(self):
        pass


app_name_map = AppNameMap(correction_file=ROOT / 'data/name_to_id_correction.yml')
my_rate = MyRate.load()
