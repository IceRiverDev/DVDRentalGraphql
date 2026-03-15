from __future__ import annotations

import enum
from typing import List, Optional

import strawberry

from app.graphql.filters.shared import (
    FloatFilter,
    IntFilter,
    SortDirection,
    StringFilter,
)
from app.graphql.types.common import PageInfo
from app.graphql.types.film import FilmType, MpaaRatingEnum


@strawberry.enum
class FilmSortField(enum.Enum):
    TITLE = "title"
    RELEASE_YEAR = "release_year"
    RENTAL_RATE = "rental_rate"
    LENGTH = "length"
    FILM_ID = "film_id"


@strawberry.input
class FilmFilter:
    film_id: Optional[IntFilter] = None
    title: Optional[StringFilter] = None
    description: Optional[StringFilter] = None
    rating: Optional[MpaaRatingEnum] = None
    rating_in: Optional[List[MpaaRatingEnum]] = None
    language_id: Optional[IntFilter] = None
    category_id: Optional[IntFilter] = None
    category_name: Optional[StringFilter] = None
    actor_id: Optional[IntFilter] = None
    actor_name: Optional[StringFilter] = None
    release_year: Optional[IntFilter] = None
    rental_rate: Optional[FloatFilter] = None
    length: Optional[IntFilter] = None
    rental_duration: Optional[IntFilter] = None
    has_special_features: Optional[bool] = None


@strawberry.input
class FilmSort:
    field: FilmSortField = FilmSortField.TITLE
    direction: SortDirection = SortDirection.ASC


@strawberry.type
class FilmConnection:
    items: List[FilmType]
    page_info: PageInfo
