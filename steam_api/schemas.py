from typing import Literal

from pydantic import BaseModel, Field


class OwnedGame(BaseModel):
    id: int = Field(..., alias='appid')
    playtime_forever: int
    playtime_windows_forever: int
    playtime_mac_forever: int
    playtime_linux_forever: int
    rtime_last_played: int
    playtime_disconnected: int


class OwnedGamesResponse(BaseModel):
    game_count: int
    games: list[OwnedGame]


class AppPriceOverview(BaseModel):
    currency: Literal[
        'RUB',
        'KRW',
        'CAD',
        'UAH',
        'SGD',
        'EUR',
        'BRL',
        'CNY',
        'USD',
        'PLN',
        'GBP',
        'HKD',
        'COP',
    ]
    initial: int
    final: int
    discount_percent: int
    initial_formatted: str
    final_formatted: str


class AppPlatforms(BaseModel):
    windows: bool
    mac: bool
    linux: bool


class AppMetacritic(BaseModel):
    score: int
    url: str


class AppCategory(BaseModel):
    id: int
    description: str


class ItemTotal(BaseModel):
    total: int


class AppReleaseData(BaseModel):
    coming_soon: bool
    date: str


class App(BaseModel):
    type: str
    name: str
    id: int | None = Field(None, alias='steam_appid')
    required_age: int
    is_free: bool
    dlc: list[int] | None = None
    detailed_description: str
    about_the_game: str
    short_description: str
    supported_languages: str | None = None
    header_image: str
    capsule_image: str
    capsule_imagev5: str
    website: str | None = None
    pc_requirements: dict
    mac_requirements: dict
    linux_requirements: dict
    developers: list[str] | None = None
    publishers: list[str]
    price_overview: AppPriceOverview | None = None
    platforms: AppPlatforms
    metacritic: AppMetacritic | None = None
    packages: list[int] | None = None
    package_groups: list[dict]
    categories: list[AppCategory]
    genres: list[AppCategory] | None = None
    screenshots: list[dict] | None = None
    movies: list[dict] | None = None
    recommendations: ItemTotal | None = None
    release_date: AppReleaseData
    ratings: dict | None = None
    support_info: dict
    background: str
    background_raw: str
    content_descriptors: dict


class ReviewsSummary(BaseModel):
    num_reviews: int
    review_score: int | None = None
    review_score_desc: str | None = None
    total_positive: int | None = None
    total_negative: int | None = None
    total_reviews: int | None = None


class ReviewAuthor(BaseModel):
    id: int = Field(..., alias='steamid')
    num_games_owned: int
    num_reviews: int
    playtime_forever: int
    playtime_last_two_weeks: int
    playtime_at_review: int | None = None
    last_played: int


class Review(BaseModel):
    id: int = Field(..., alias='recommendationid')
    author: ReviewAuthor
    language: str
    review: str | None = None
    timestamp_created: int
    timestamp_updated: int
    voted_up: bool
    votes_up: int
    votes_funny: int
    weighted_vote_score: float
    comment_count: int
    steam_purchase: bool
    recieved_for_free: bool | None = None
    written_during_early_access: bool
    hidden_in_steam_china: bool
    steam_china_location: str
    developer_response: str | None = None
    timestamp_dev_responded: int | None = None


class ReviewsResponse(BaseModel):
    success: bool
    query_summary: ReviewsSummary
    reviews: list[Review]
    cursor: str | None = None


class AppInfoOuter(BaseModel):
    success: bool
    data: App | None = None


class AppInfoResponse(BaseModel):
    __root__: dict[str, AppInfoOuter]
