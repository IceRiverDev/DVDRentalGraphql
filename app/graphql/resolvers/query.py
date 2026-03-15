from __future__ import annotations

import math
from decimal import Decimal
from typing import List, Optional

import strawberry
from sqlalchemy import func, select, text
from strawberry.types import Info

from app.graphql.dataloaders import (
    _actor_to_type,
    _category_to_type,
    _customer_to_type,
    _film_to_type,
    _inventory_to_type,
    _language_to_type,
    _payment_to_type,
    _rental_to_type,
)
from app.graphql.filters.actor_filter import (
    ActorConnection,
    ActorFilter,
    ActorSort,
    ActorSortField,
)
from app.graphql.filters.customer_filter import (
    CustomerConnection,
    CustomerFilter,
    CustomerSort,
    CustomerSortField,
)
from app.graphql.filters.film_filter import (
    FilmConnection,
    FilmFilter,
    FilmSort,
    FilmSortField,
)
from app.graphql.filters.inventory_filter import InventoryConnection, InventoryFilter
from app.graphql.filters.payment_filter import (
    PaymentConnection,
    PaymentFilter,
    PaymentSort,
    PaymentSortField,
)
from app.graphql.filters.rental_filter import (
    RentalConnection,
    RentalFilter,
    RentalSort,
    RentalSortField,
)
from app.graphql.filters.shared import (
    apply_date_filter,
    apply_datetime_filter,
    apply_float_filter,
    apply_int_filter,
    apply_string_filter,
)
from app.graphql.types.catalog import ActorType, CategoryType, LanguageType
from app.graphql.types.common import PageInfo
from app.graphql.types.film import FilmType
from app.graphql.types.geography import CountryType
from app.graphql.types.people import CustomerType, StoreType
from app.graphql.types.transactions import (
    InventoryType,
    PaymentSummaryType,
    PaymentType,
    RentalType,
)
from app.models.models import (
    Actor,
    Category,
    Customer,
    Film,
    FilmActor,
    FilmCategory,
    Inventory,
    Language,
    Payment,
    Rental,
    Store,
)


def _make_page_info(total: int, page: int, page_size: int) -> PageInfo:
    total_pages = max(1, math.ceil(total / page_size))
    return PageInfo(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


def _offset(page: int, page_size: int) -> int:
    return (page - 1) * page_size


@strawberry.type
class Query:
    # ── Films ─────────────────────────────────────────────────────────────────

    @strawberry.field
    async def films(
        self,
        info: Info,
        filter: Optional[FilmFilter] = None,
        sort: Optional[FilmSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> FilmConnection:
        async with info.context.session_factory() as db:
            q = select(Film)

            if filter:
                q = apply_int_filter(q, Film.film_id, filter.film_id)
                q = apply_string_filter(q, Film.title, filter.title)
                q = apply_string_filter(q, Film.description, filter.description)
                if filter.rating is not None:
                    from app.models.models import MpaaRating as OrmRating

                    q = q.where(Film.rating == OrmRating(filter.rating.value))
                if filter.rating_in is not None:
                    from app.models.models import MpaaRating as OrmRating

                    q = q.where(
                        Film.rating.in_([OrmRating(r.value) for r in filter.rating_in])
                    )
                if filter.language_id is not None:
                    q = apply_int_filter(q, Film.language_id, filter.language_id)
                if filter.category_id is not None or filter.category_name is not None:
                    q = q.join(FilmCategory, Film.film_id == FilmCategory.film_id)
                    if filter.category_id is not None:
                        q = apply_int_filter(
                            q, FilmCategory.category_id, filter.category_id
                        )
                    if filter.category_name is not None:
                        q = q.join(
                            Category, FilmCategory.category_id == Category.category_id
                        )
                        q = apply_string_filter(q, Category.name, filter.category_name)
                if filter.actor_id is not None or filter.actor_name is not None:
                    q = q.join(FilmActor, Film.film_id == FilmActor.film_id)
                    if filter.actor_id is not None:
                        q = apply_int_filter(q, FilmActor.actor_id, filter.actor_id)
                    if filter.actor_name is not None:
                        q = q.join(Actor, FilmActor.actor_id == Actor.actor_id)
                        q = apply_string_filter(
                            q,
                            Actor.first_name + " " + Actor.last_name,
                            filter.actor_name,
                        )
                q = apply_int_filter(q, Film.release_year, filter.release_year)
                q = apply_float_filter(q, Film.rental_rate, filter.rental_rate)
                q = apply_int_filter(q, Film.length, filter.length)
                q = apply_int_filter(q, Film.rental_duration, filter.rental_duration)
                if filter.has_special_features is not None:
                    if filter.has_special_features:
                        q = q.where(Film.special_features.is_not(None))
                    else:
                        q = q.where(Film.special_features.is_(None))

            q = q.distinct()

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            if sort:
                col_map = {
                    FilmSortField.TITLE: Film.title,
                    FilmSortField.RELEASE_YEAR: Film.release_year,
                    FilmSortField.RENTAL_RATE: Film.rental_rate,
                    FilmSortField.LENGTH: Film.length,
                    FilmSortField.FILM_ID: Film.film_id,
                }
                col = col_map[sort.field]
                q = q.order_by(
                    col.asc() if sort.direction.value == "asc" else col.desc()
                )
            else:
                q = q.order_by(Film.title.asc())

            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return FilmConnection(
                items=[_film_to_type(f) for f in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def film(self, info: Info, film_id: int) -> Optional[FilmType]:
        async with info.context.session_factory() as db:
            result = await db.execute(select(Film).where(Film.film_id == film_id))
            f = result.scalar_one_or_none()
            return _film_to_type(f) if f else None

        # ── Actors ────────────────────────────────────────────────────────────────

    @strawberry.field
    async def actors(
        self,
        info: Info,
        filter: Optional[ActorFilter] = None,
        sort: Optional[ActorSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ActorConnection:
        async with info.context.session_factory() as db:
            q = select(Actor)

            if filter:
                q = apply_int_filter(q, Actor.actor_id, filter.actor_id)
                if filter.name is not None:
                    q = apply_string_filter(
                        q, Actor.first_name + " " + Actor.last_name, filter.name
                    )
                q = apply_string_filter(q, Actor.first_name, filter.first_name)
                q = apply_string_filter(q, Actor.last_name, filter.last_name)
                if filter.film_id is not None:
                    q = q.join(FilmActor, Actor.actor_id == FilmActor.actor_id)
                    q = apply_int_filter(q, FilmActor.film_id, filter.film_id)

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            if sort:
                col_map = {
                    ActorSortField.FIRST_NAME: Actor.first_name,
                    ActorSortField.LAST_NAME: Actor.last_name,
                    ActorSortField.ACTOR_ID: Actor.actor_id,
                }
                col = col_map[sort.field]
                q = q.order_by(
                    col.asc() if sort.direction.value == "asc" else col.desc()
                )
            else:
                q = q.order_by(Actor.last_name.asc())

            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return ActorConnection(
                items=[_actor_to_type(a) for a in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def actor(self, info: Info, actor_id: int) -> Optional[ActorType]:
        async with info.context.session_factory() as db:
            result = await db.execute(select(Actor).where(Actor.actor_id == actor_id))
            a = result.scalar_one_or_none()
            return _actor_to_type(a) if a else None

        # ── Customers ─────────────────────────────────────────────────────────────

    @strawberry.field
    async def customers(
        self,
        info: Info,
        filter: Optional[CustomerFilter] = None,
        sort: Optional[CustomerSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CustomerConnection:
        async with info.context.session_factory() as db:
            q = select(Customer)

            if filter:
                q = apply_int_filter(q, Customer.customer_id, filter.customer_id)
                if filter.name is not None:
                    q = apply_string_filter(
                        q, Customer.first_name + " " + Customer.last_name, filter.name
                    )
                q = apply_string_filter(q, Customer.email, filter.email)
                if filter.active is not None:
                    q = q.where(Customer.activebool == filter.active)
                q = apply_int_filter(q, Customer.store_id, filter.store_id)
                q = apply_date_filter(q, Customer.create_date, filter.create_date)

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            if sort:
                col_map = {
                    CustomerSortField.FIRST_NAME: Customer.first_name,
                    CustomerSortField.LAST_NAME: Customer.last_name,
                    CustomerSortField.CUSTOMER_ID: Customer.customer_id,
                    CustomerSortField.CREATE_DATE: Customer.create_date,
                    CustomerSortField.EMAIL: Customer.email,
                }
                col = col_map[sort.field]
                q = q.order_by(
                    col.asc() if sort.direction.value == "asc" else col.desc()
                )
            else:
                q = q.order_by(Customer.last_name.asc())

            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return CustomerConnection(
                items=[_customer_to_type(c) for c in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def customer(self, info: Info, customer_id: int) -> Optional[CustomerType]:
        async with info.context.session_factory() as db:
            result = await db.execute(
                select(Customer).where(Customer.customer_id == customer_id)
            )
            c = result.scalar_one_or_none()
            return _customer_to_type(c) if c else None

        # ── Rentals ───────────────────────────────────────────────────────────────

    @strawberry.field
    async def rentals(
        self,
        info: Info,
        filter: Optional[RentalFilter] = None,
        sort: Optional[RentalSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> RentalConnection:
        async with info.context.session_factory() as db:
            q = select(Rental)

            if filter:
                q = apply_int_filter(q, Rental.rental_id, filter.rental_id)
                q = apply_datetime_filter(q, Rental.rental_date, filter.rental_date)
                q = apply_int_filter(q, Rental.customer_id, filter.customer_id)
                q = apply_int_filter(q, Rental.staff_id, filter.staff_id)
                q = apply_int_filter(q, Rental.inventory_id, filter.inventory_id)
                if filter.film_id is not None:
                    q = q.join(Inventory, Rental.inventory_id == Inventory.inventory_id)
                    q = apply_int_filter(q, Inventory.film_id, filter.film_id)
                if filter.is_returned is not None:
                    if filter.is_returned:
                        q = q.where(Rental.return_date.is_not(None))
                    else:
                        q = q.where(Rental.return_date.is_(None))
                if filter.is_overdue is not None and filter.is_overdue:
                    q = (
                        q.join(Inventory, Rental.inventory_id == Inventory.inventory_id)
                        .join(Film, Inventory.film_id == Film.film_id)
                        .where(Rental.return_date.is_(None))
                        .where(
                            Rental.rental_date
                            + text("INTERVAL '1 day' * film.rental_duration")
                            < func.now()
                        )
                    )

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            if sort:
                col_map = {
                    RentalSortField.RENTAL_DATE: Rental.rental_date,
                    RentalSortField.RETURN_DATE: Rental.return_date,
                    RentalSortField.RENTAL_ID: Rental.rental_id,
                    RentalSortField.CUSTOMER_ID: Rental.customer_id,
                }
                col = col_map[sort.field]
                q = q.order_by(
                    col.asc() if sort.direction.value == "asc" else col.desc()
                )
            else:
                q = q.order_by(Rental.rental_date.desc())

            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return RentalConnection(
                items=[_rental_to_type(r) for r in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def rental(self, info: Info, rental_id: int) -> Optional[RentalType]:
        async with info.context.session_factory() as db:
            result = await db.execute(
                select(Rental).where(Rental.rental_id == rental_id)
            )
            r = result.scalar_one_or_none()
            return _rental_to_type(r) if r else None

    @strawberry.field
    async def overdue_rentals(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
    ) -> RentalConnection:
        async with info.context.session_factory() as db:
            q = (
                select(Rental)
                .join(Inventory, Rental.inventory_id == Inventory.inventory_id)
                .join(Film, Inventory.film_id == Film.film_id)
                .where(Rental.return_date.is_(None))
                .where(
                    Rental.rental_date + text("INTERVAL '1 day' * film.rental_duration")
                    < func.now()
                )
            )

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            q = q.order_by(Rental.rental_date.asc())
            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return RentalConnection(
                items=[_rental_to_type(r) for r in rows],
                page_info=_make_page_info(total, page, page_size),
            )

        # ── Payments ──────────────────────────────────────────────────────────────

    @strawberry.field
    async def payments(
        self,
        info: Info,
        filter: Optional[PaymentFilter] = None,
        sort: Optional[PaymentSort] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaymentConnection:
        async with info.context.session_factory() as db:
            q = select(Payment)

            if filter:
                q = apply_int_filter(q, Payment.payment_id, filter.payment_id)
                q = apply_int_filter(q, Payment.customer_id, filter.customer_id)
                q = apply_int_filter(q, Payment.staff_id, filter.staff_id)
                q = apply_int_filter(q, Payment.rental_id, filter.rental_id)
                q = apply_float_filter(q, Payment.amount, filter.amount)
                q = apply_datetime_filter(q, Payment.payment_date, filter.payment_date)

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            if sort:
                col_map = {
                    PaymentSortField.PAYMENT_DATE: Payment.payment_date,
                    PaymentSortField.AMOUNT: Payment.amount,
                    PaymentSortField.PAYMENT_ID: Payment.payment_id,
                    PaymentSortField.CUSTOMER_ID: Payment.customer_id,
                }
                col = col_map[sort.field]
                q = q.order_by(
                    col.asc() if sort.direction.value == "asc" else col.desc()
                )
            else:
                q = q.order_by(Payment.payment_date.desc())

            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return PaymentConnection(
                items=[_payment_to_type(p) for p in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def payment(self, info: Info, payment_id: int) -> Optional[PaymentType]:
        async with info.context.session_factory() as db:
            result = await db.execute(
                select(Payment).where(Payment.payment_id == payment_id)
            )
            p = result.scalar_one_or_none()
            return _payment_to_type(p) if p else None

    @strawberry.field
    async def payment_summary(
        self,
        info: Info,
        customer_id: Optional[int] = None,
    ) -> PaymentSummaryType:
        async with info.context.session_factory() as db:
            q = select(
                func.count(Payment.payment_id).label("total_count"),
                func.sum(Payment.amount).label("total_amount"),
                func.avg(Payment.amount).label("average_amount"),
                func.min(Payment.amount).label("min_amount"),
                func.max(Payment.amount).label("max_amount"),
            )
            if customer_id is not None:
                q = q.where(Payment.customer_id == customer_id)
            row = (await db.execute(q)).one()
            return PaymentSummaryType(
                total_count=row.total_count or 0,
                total_amount=Decimal(str(row.total_amount or 0)),
                average_amount=Decimal(str(row.average_amount or 0)),
                min_amount=Decimal(str(row.min_amount or 0)),
                max_amount=Decimal(str(row.max_amount or 0)),
            )

        # ── Inventory ─────────────────────────────────────────────────────────────

    @strawberry.field
    async def inventories(
        self,
        info: Info,
        filter: Optional[InventoryFilter] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InventoryConnection:
        async with info.context.session_factory() as db:
            q = select(Inventory)

            if filter:
                q = apply_int_filter(q, Inventory.inventory_id, filter.inventory_id)
                q = apply_int_filter(q, Inventory.film_id, filter.film_id)
                q = apply_int_filter(q, Inventory.store_id, filter.store_id)
                if filter.is_available is not None:
                    active_rental = (
                        select(Rental.rental_id)
                        .where(Rental.inventory_id == Inventory.inventory_id)
                        .where(Rental.return_date.is_(None))
                        .exists()
                    )
                    if filter.is_available:
                        q = q.where(~active_rental)
                    else:
                        q = q.where(active_rental)

            count_q = select(func.count()).select_from(q.subquery())
            total = (await db.execute(count_q)).scalar_one()

            q = q.order_by(Inventory.inventory_id.asc())
            q = q.offset(_offset(page, page_size)).limit(page_size)
            rows = (await db.execute(q)).scalars().all()

            return InventoryConnection(
                items=[_inventory_to_type(i) for i in rows],
                page_info=_make_page_info(total, page, page_size),
            )

    @strawberry.field
    async def inventory(self, info: Info, inventory_id: int) -> Optional[InventoryType]:
        async with info.context.session_factory() as db:
            result = await db.execute(
                select(Inventory).where(Inventory.inventory_id == inventory_id)
            )
            i = result.scalar_one_or_none()
            return _inventory_to_type(i) if i else None

        # ── Reference data ────────────────────────────────────────────────────────

    @strawberry.field
    async def categories(self, info: Info) -> List[CategoryType]:
        async with info.context.session_factory() as db:
            rows = (
                (await db.execute(select(Category).order_by(Category.name)))
                .scalars()
                .all()
            )
            return [_category_to_type(c) for c in rows]

    @strawberry.field
    async def languages(self, info: Info) -> List[LanguageType]:
        async with info.context.session_factory() as db:
            rows = (
                (await db.execute(select(Language).order_by(Language.name)))
                .scalars()
                .all()
            )
            return [_language_to_type(l) for l in rows]

    @strawberry.field
    async def countries(self, info: Info) -> List[CountryType]:
        async with info.context.session_factory() as db:
            from app.models.models import Country as CountryModel

            rows = (
                (await db.execute(select(CountryModel).order_by(CountryModel.country)))
                .scalars()
                .all()
            )
            return [
                CountryType(
                    country_id=c.country_id,
                    country=c.country,
                    last_update=c.last_update,
                )
                for c in rows
            ]

    @strawberry.field
    async def stores(self, info: Info) -> List[StoreType]:
        async with info.context.session_factory() as db:
            rows = (
                (await db.execute(select(Store).order_by(Store.store_id)))
                .scalars()
                .all()
            )
            return [
                StoreType(
                    store_id=s.store_id,
                    manager_staff_id=s.manager_staff_id,
                    address_id=s.address_id,
                    last_update=s.last_update,
                )
                for s in rows
            ]
