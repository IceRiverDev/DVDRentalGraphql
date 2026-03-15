from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from strawberry.types import Info

if TYPE_CHECKING:
    from app.graphql.types.catalog import ActorType, CategoryType, LanguageType
    from app.graphql.types.transactions import InventoryType


@strawberry.enum
class MpaaRatingEnum(enum.StrEnum):
    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"


@strawberry.type
class FilmType:
    film_id: int
    title: str
    description: Optional[str]
    release_year: Optional[int]
    language_id: int
    rental_duration: int
    rental_rate: Decimal
    length: Optional[int]
    replacement_cost: Decimal
    rating: Optional[MpaaRatingEnum]
    special_features: Optional[List[str]]
    last_update: datetime

    @strawberry.field
    async def language(
        self, info: Info
    ) -> Optional[
        Annotated["LanguageType", strawberry.lazy("app.graphql.types.catalog")]
    ]:
        return await info.context.loaders.language.load(self.language_id)

    @strawberry.field
    async def actors(
        self, info: Info
    ) -> List[Annotated["ActorType", strawberry.lazy("app.graphql.types.catalog")]]:
        return await info.context.loaders.film_actors.load(self.film_id)

    @strawberry.field
    async def categories(
        self, info: Info
    ) -> List[Annotated["CategoryType", strawberry.lazy("app.graphql.types.catalog")]]:
        return await info.context.loaders.film_categories.load(self.film_id)

    @strawberry.field
    async def inventories(
        self, info: Info
    ) -> List[Annotated["InventoryType", strawberry.lazy("app.graphql.types.transactions")]]:
        return await info.context.loaders.film_inventories.load(self.film_id)
