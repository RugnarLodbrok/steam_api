from typing import Iterator, cast

import requests
from requests import ConnectTimeout

from steam_api.cache import cache
from steam_api.cache.serializers import SerializerJson
from steam_api.common import AnyDict
from steam_api.config import config
from steam_api.schemas import (
    App,
    AppInfoResponse,
    OwnedGamesResponse,
    Review,
    ReviewsResponse,
    ReviewsSummary,
)
from steam_api.utils import retry

CONN_TIMEOUT = 5
READ_TIMEOUT = 10
BACKOFF_TIMEOUT = 3

TIMEOUT_TUPLE = (CONN_TIMEOUT, READ_TIMEOUT)


class AppNotFound(Exception):
    pass


class ReviewCollision(Exception):
    pass


class NotFound(Exception):
    pass


class Client:
    STORE_API = 'https://store.steampowered.com'
    STEAM_API = 'https://api.steampowered.com'

    def __init__(self, api_key: str):
        self.api_key = api_key

    @cache('get_app_info', model=App)
    def get_app_info(self, app_id: int) -> App:
        # raise NotFound('disable fetch')
        response = requests.get(
            f'{self.STORE_API}/api/appdetails?appids={app_id}',
            timeout=TIMEOUT_TUPLE,
        )
        response.raise_for_status()
        raw = AppInfoResponse.parse_raw(response.text)
        assert set(raw.root) == {str(app_id)}
        outer = raw.root[str(app_id)]
        if not outer.success:
            raise NotFound(f'app {app_id} retrieve failed')
        if not outer.data:
            raise NotFound(f'app {app_id} empty data')
        return cast(App, outer.data)

    @cache('player_owned_games', OwnedGamesResponse)
    def get_player_owned_games(self, steam_id: int) -> OwnedGamesResponse:
        response = requests.get(
            url=f'{self.STEAM_API}/IPlayerService/GetOwnedGames/v0001/',
            params={
                'key': self.api_key,
                'steamid': steam_id,
                'format': 'json',
            },
            timeout=TIMEOUT_TUPLE,
        )
        response.raise_for_status()
        return OwnedGamesResponse.parse_obj(response.json()['response'])

    def get_total_reviews(self, app_id: int) -> int:
        return self.get_review_summary(app_id).total_reviews

    @cache('review_summary', model=ReviewsSummary)
    def get_review_summary(self, app_id: int) -> ReviewsSummary:
        return self._get_reviews(app_id).query_summary

    @cache('reviews', model=Review)
    def get_reviews(self, app_id: int) -> Iterator[Review]:
        ids = set()
        cursor = '*'
        while cursor:
            batch = self._get_reviews(app_id, cursor=cursor)
            if not batch.reviews:
                break
            for review in batch.reviews:
                if review.id in ids:
                    raise ReviewCollision((review.id, ids))
                ids.add(review.id)
                yield review
            cursor = batch.cursor
        else:
            print('MISSING CURSOR')

    @retry(ConnectTimeout, n=30, backoff_time=BACKOFF_TIMEOUT)
    def _get_reviews(self, app_id: int, cursor: str = '*') -> ReviewsResponse:
        response = requests.get(
            f'{self.STORE_API}/appreviews/{app_id}',
            params={
                'json': 1,
                'language': 'all',
                # this means ordering, not filter. Cursor won't work with default 'all'
                'filter': 'recent',
                'review_type': 'all',
                'appids': app_id,
                'cursor': cursor,
                'num_per_page': 100,
                'filter_offtopic_activity': 0,
            },
            timeout=TIMEOUT_TUPLE,
        )
        response.raise_for_status()
        result = ReviewsResponse.parse_obj(response.json())
        assert result.success
        return result

    @cache('all_apps', key=None, serializer=SerializerJson())
    def get_all_apps(self) -> list[AnyDict]:
        response = requests.get(
            f'{self.STEAM_API}/ISteamApps/GetAppList/v2/',
            timeout=TIMEOUT_TUPLE,
        )
        response.raise_for_status()
        return response.json()['applist']['apps']


client = Client(config.STEAM_API_KEY)
