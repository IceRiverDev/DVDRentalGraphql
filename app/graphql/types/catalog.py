from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, List

import strawberry
from strawberry.types import Info

if TYPE_CHECKING:
    from app.graphql.types.film import FilmType


@strawberry.type
class LanguageType:
    language_id: int
    name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self, info: Info
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        return await info.context.loaders.language_films.load(self.language_id)


@strawberry.type
class CategoryType:
    category_id: int
    name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self, info: Info
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        return await info.context.loaders.category_films.load(self.category_id)


@strawberry.type
class ActorType:
    actor_id: int
    first_name: str
    last_name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self, info: Info
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        return await info.context.loaders.actor_films.load(self.actor_id)
