from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from sqlalchemy import select
from strawberry.types import Info

from app.graphql.filters.film_filter import FilmFilter
from app.graphql.filters.shared import apply_float_filter, apply_int_filter, apply_string_filter

if TYPE_CHECKING:
    from app.graphql.types.film import FilmType


def _apply_film_filter(q, f: FilmFilter):
    from app.models.models import Film, FilmActor, FilmCategory, MpaaRating

    q = apply_int_filter(q, Film.film_id, f.film_id)
    q = apply_string_filter(q, Film.title, f.title)
    q = apply_string_filter(q, Film.description, f.description)
    if f.rating is not None:
        q = q.where(Film.rating == MpaaRating(f.rating.value))
    if f.rating_in is not None:
        q = q.where(Film.rating.in_([MpaaRating(r.value) for r in f.rating_in]))
    q = apply_int_filter(q, Film.length, f.length)
    q = apply_float_filter(q, Film.rental_rate, f.rental_rate)
    q = apply_int_filter(q, Film.release_year, f.release_year)
    q = apply_int_filter(q, Film.rental_duration, f.rental_duration)
    if f.has_special_features is True:
        q = q.where(Film.special_features.is_not(None))
    elif f.has_special_features is False:
        q = q.where(Film.special_features.is_(None))
    return q


@strawberry.type
class LanguageType:
    language_id: int
    name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self,
        info: Info,
        filter: Optional[FilmFilter] = None,
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        if filter is None:
            return await info.context.loaders.language_films.load(self.language_id)
        from app.graphql.dataloaders import _film_to_type
        from app.models.models import Film

        async with info.context.session_factory() as db:
            q = select(Film).where(Film.language_id == self.language_id)
            q = _apply_film_filter(q, filter)
            result = await db.execute(q)
            return [_film_to_type(f) for f in result.scalars().all()]


@strawberry.type
class CategoryType:
    category_id: int
    name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self,
        info: Info,
        filter: Optional[FilmFilter] = None,
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        if filter is None:
            return await info.context.loaders.category_films.load(self.category_id)
        from app.graphql.dataloaders import _film_to_type
        from app.models.models import Film, FilmCategory

        async with info.context.session_factory() as db:
            q = (
                select(Film)
                .join(FilmCategory, FilmCategory.film_id == Film.film_id)
                .where(FilmCategory.category_id == self.category_id)
            )
            q = _apply_film_filter(q, filter)
            result = await db.execute(q)
            return [_film_to_type(f) for f in result.scalars().all()]


@strawberry.type
class ActorType:
    actor_id: int
    first_name: str
    last_name: str
    last_update: datetime

    @strawberry.field
    async def films(
        self,
        info: Info,
        filter: Optional[FilmFilter] = None,
    ) -> List[Annotated["FilmType", strawberry.lazy("app.graphql.types.film")]]:
        if filter is None:
            return await info.context.loaders.actor_films.load(self.actor_id)
        from app.graphql.dataloaders import _film_to_type
        from app.models.models import Film, FilmActor

        async with info.context.session_factory() as db:
            q = (
                select(Film)
                .join(FilmActor, FilmActor.film_id == Film.film_id)
                .where(FilmActor.actor_id == self.actor_id)
            )
            q = _apply_film_filter(q, filter)
            result = await db.execute(q)
            return [_film_to_type(f) for f in result.scalars().all()]
