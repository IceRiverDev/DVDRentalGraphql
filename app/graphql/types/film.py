from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, List, Optional

import strawberry
from sqlalchemy import select
from strawberry.types import Info

from app.graphql.filters.actor_filter import ActorFilter
from app.graphql.filters.inventory_filter import InventoryFilter
from app.graphql.filters.shared import (
    CategoryFilter,
    MpaaRatingEnum,
    apply_int_filter,
    apply_string_filter,
)

if TYPE_CHECKING:
    from app.graphql.types.catalog import ActorType, CategoryType, LanguageType
    from app.graphql.types.transactions import InventoryType


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
        self,
        info: Info,
        filter: Optional[ActorFilter] = None,
    ) -> List[Annotated["ActorType", strawberry.lazy("app.graphql.types.catalog")]]:
        if filter is None:
            return await info.context.loaders.film_actors.load(self.film_id)
        from app.graphql.dataloaders import _actor_to_type
        from app.models.models import Actor, FilmActor

        async with info.context.session_factory() as db:
            q = (
                select(Actor)
                .join(FilmActor, FilmActor.actor_id == Actor.actor_id)
                .where(FilmActor.film_id == self.film_id)
            )
            q = apply_int_filter(q, Actor.actor_id, filter.actor_id)
            q = apply_string_filter(q, Actor.first_name, filter.first_name)
            q = apply_string_filter(q, Actor.last_name, filter.last_name)
            result = await db.execute(q)
            return [_actor_to_type(a) for a in result.scalars().all()]

    @strawberry.field
    async def categories(
        self,
        info: Info,
        filter: Optional[CategoryFilter] = None,
    ) -> List[Annotated["CategoryType", strawberry.lazy("app.graphql.types.catalog")]]:
        if filter is None:
            return await info.context.loaders.film_categories.load(self.film_id)
        from app.graphql.dataloaders import _category_to_type
        from app.models.models import Category, FilmCategory

        async with info.context.session_factory() as db:
            q = (
                select(Category)
                .join(FilmCategory, FilmCategory.category_id == Category.category_id)
                .where(FilmCategory.film_id == self.film_id)
            )
            q = apply_int_filter(q, Category.category_id, filter.category_id)
            q = apply_string_filter(q, Category.name, filter.name)
            result = await db.execute(q)
            return [_category_to_type(c) for c in result.scalars().all()]

    @strawberry.field
    async def inventories(
        self,
        info: Info,
        filter: Optional[InventoryFilter] = None,
    ) -> List[Annotated["InventoryType", strawberry.lazy("app.graphql.types.transactions")]]:
        if filter is None:
            return await info.context.loaders.film_inventories.load(self.film_id)
        from app.graphql.dataloaders import _inventory_to_type
        from app.models.models import Inventory, Rental

        async with info.context.session_factory() as db:
            q = select(Inventory).where(Inventory.film_id == self.film_id)
            q = apply_int_filter(q, Inventory.inventory_id, filter.inventory_id)
            q = apply_int_filter(q, Inventory.store_id, filter.store_id)
            if filter.is_available is True:
                rented = select(Rental.inventory_id).where(Rental.return_date.is_(None))
                q = q.where(Inventory.inventory_id.not_in(rented))
            elif filter.is_available is False:
                rented = select(Rental.inventory_id).where(Rental.return_date.is_(None))
                q = q.where(Inventory.inventory_id.in_(rented))
            result = await db.execute(q)
            return [_inventory_to_type(i) for i in result.scalars().all()]
