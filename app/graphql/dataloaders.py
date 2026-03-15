from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

from sqlalchemy import select
from strawberry.dataloader import DataLoader

from app.graphql.types.catalog import ActorType, CategoryType, LanguageType
from app.graphql.filters.shared import MpaaRatingEnum
from app.graphql.types.film import FilmType
from app.graphql.types.geography import AddressType
from app.graphql.types.people import CustomerType
from app.graphql.types.transactions import InventoryType, PaymentType, RentalType
from app.models.models import (
    Actor,
    Address,
    Category,
    Customer,
    Film,
    FilmActor,
    FilmCategory,
    Inventory,
    Language,
    MpaaRating,
    Payment,
    Rental,
)


def _orm_rating_to_enum(rating: MpaaRating | None) -> MpaaRatingEnum | None:
    if rating is None:
        return None
    return MpaaRatingEnum(rating.value)


def _film_to_type(f: Film) -> FilmType:
    return FilmType(
        film_id=f.film_id,
        title=f.title,
        description=f.description,
        release_year=f.release_year,
        language_id=f.language_id,
        rental_duration=f.rental_duration,
        rental_rate=f.rental_rate,
        length=f.length,
        replacement_cost=f.replacement_cost,
        rating=_orm_rating_to_enum(f.rating),
        special_features=f.special_features,
        last_update=f.last_update,
    )


def _language_to_type(l: Language) -> LanguageType:
    return LanguageType(
        language_id=l.language_id, name=l.name, last_update=l.last_update
    )


def _actor_to_type(a: Actor) -> ActorType:
    return ActorType(
        actor_id=a.actor_id,
        first_name=a.first_name,
        last_name=a.last_name,
        last_update=a.last_update,
    )


def _category_to_type(c: Category) -> CategoryType:
    return CategoryType(
        category_id=c.category_id, name=c.name, last_update=c.last_update
    )


def _address_to_type(a: Address) -> AddressType:
    return AddressType(
        address_id=a.address_id,
        address=a.address,
        address2=a.address2,
        district=a.district,
        city_id=a.city_id,
        postal_code=a.postal_code,
        phone=a.phone,
        last_update=a.last_update,
    )


def _customer_to_type(c: Customer) -> CustomerType:
    return CustomerType(
        customer_id=c.customer_id,
        store_id=c.store_id,
        first_name=c.first_name,
        last_name=c.last_name,
        email=c.email,
        address_id=c.address_id,
        activebool=c.activebool,
        create_date=c.create_date,
        last_update=c.last_update,
        active=c.active,
    )


def _inventory_to_type(i: Inventory) -> InventoryType:
    return InventoryType(
        inventory_id=i.inventory_id,
        film_id=i.film_id,
        store_id=i.store_id,
        last_update=i.last_update,
    )


def _rental_to_type(r: Rental) -> RentalType:
    return RentalType(
        rental_id=r.rental_id,
        rental_date=r.rental_date,
        inventory_id=r.inventory_id,
        customer_id=r.customer_id,
        return_date=r.return_date,
        staff_id=r.staff_id,
        last_update=r.last_update,
    )


def _payment_to_type(p: Payment) -> PaymentType:
    return PaymentType(
        payment_id=p.payment_id,
        customer_id=p.customer_id,
        staff_id=p.staff_id,
        rental_id=p.rental_id,
        amount=p.amount,
        payment_date=p.payment_date,
    )


@dataclass
class DataLoaders:
    def __post_init__(self) -> None:
        from app.core.database import AsyncSessionLocal

        self._session_factory = AsyncSessionLocal

        self.language: DataLoader[int, LanguageType | None] = DataLoader(
            load_fn=self._load_languages
        )
        self.film: DataLoader[int, FilmType | None] = DataLoader(
            load_fn=self._load_films
        )
        self.film_actors: DataLoader[int, list[ActorType]] = DataLoader(
            load_fn=self._load_actors_by_film_id
        )
        self.film_categories: DataLoader[int, list[CategoryType]] = DataLoader(
            load_fn=self._load_categories_by_film_id
        )
        self.address: DataLoader[int, AddressType | None] = DataLoader(
            load_fn=self._load_addresses
        )
        self.customer: DataLoader[int, CustomerType | None] = DataLoader(
            load_fn=self._load_customers
        )
        self.customer_rentals: DataLoader[int, list[RentalType]] = DataLoader(
            load_fn=self._load_rentals_by_customer_id
        )
        self.inventory: DataLoader[int, InventoryType | None] = DataLoader(
            load_fn=self._load_inventories
        )
        self.rental_payments: DataLoader[int, list[PaymentType]] = DataLoader(
            load_fn=self._load_payments_by_rental_id
        )
        # ── Reverse relations ─────────────────────────────────────────────────
        self.rental: DataLoader[int, RentalType | None] = DataLoader(
            load_fn=self._load_rentals
        )
        self.actor_films: DataLoader[int, list[FilmType]] = DataLoader(
            load_fn=self._load_films_by_actor_id
        )
        self.category_films: DataLoader[int, list[FilmType]] = DataLoader(
            load_fn=self._load_films_by_category_id
        )
        self.language_films: DataLoader[int, list[FilmType]] = DataLoader(
            load_fn=self._load_films_by_language_id
        )
        self.film_inventories: DataLoader[int, list[InventoryType]] = DataLoader(
            load_fn=self._load_inventories_by_film_id
        )
        self.inventory_rentals: DataLoader[int, list[RentalType]] = DataLoader(
            load_fn=self._load_rentals_by_inventory_id
        )
        self.customer_payments: DataLoader[int, list[PaymentType]] = DataLoader(
            load_fn=self._load_payments_by_customer_id
        )

    async def _load_languages(self, ids: Sequence[int]) -> list[LanguageType | None]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Language).where(Language.language_id.in_(ids))
            )
            mapping = {
                l.language_id: _language_to_type(l) for l in result.scalars().all()
            }
        return [mapping.get(id_) for id_ in ids]

    async def _load_films(self, ids: Sequence[int]) -> list[FilmType | None]:
        async with self._session_factory() as db:
            result = await db.execute(select(Film).where(Film.film_id.in_(ids)))
            mapping = {f.film_id: _film_to_type(f) for f in result.scalars().all()}
        return [mapping.get(id_) for id_ in ids]

    async def _load_actors_by_film_id(
        self, film_ids: Sequence[int]
    ) -> list[list[ActorType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(FilmActor, Actor)
                .join(Actor, FilmActor.actor_id == Actor.actor_id)
                .where(FilmActor.film_id.in_(film_ids))
            )
            rows = result.all()
        mapping: dict[int, list[ActorType]] = defaultdict(list)
        for film_actor, actor in rows:
            mapping[film_actor.film_id].append(_actor_to_type(actor))
        return [mapping.get(fid, []) for fid in film_ids]

    async def _load_categories_by_film_id(
        self, film_ids: Sequence[int]
    ) -> list[list[CategoryType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(FilmCategory, Category)
                .join(Category, FilmCategory.category_id == Category.category_id)
                .where(FilmCategory.film_id.in_(film_ids))
            )
            rows = result.all()
        mapping: dict[int, list[CategoryType]] = defaultdict(list)
        for film_cat, cat in rows:
            mapping[film_cat.film_id].append(_category_to_type(cat))
        return [mapping.get(fid, []) for fid in film_ids]

    async def _load_addresses(self, ids: Sequence[int]) -> list[AddressType | None]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Address).where(Address.address_id.in_(ids))
            )
            mapping = {
                a.address_id: _address_to_type(a) for a in result.scalars().all()
            }
        return [mapping.get(id_) for id_ in ids]

    async def _load_customers(self, ids: Sequence[int]) -> list[CustomerType | None]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Customer).where(Customer.customer_id.in_(ids))
            )
            mapping = {
                c.customer_id: _customer_to_type(c) for c in result.scalars().all()
            }
        return [mapping.get(id_) for id_ in ids]

    async def _load_rentals_by_customer_id(
        self, customer_ids: Sequence[int]
    ) -> list[list[RentalType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Rental).where(Rental.customer_id.in_(customer_ids))
            )
            rentals = result.scalars().all()
        mapping: dict[int, list[RentalType]] = defaultdict(list)
        for r in rentals:
            mapping[r.customer_id].append(_rental_to_type(r))
        return [mapping.get(cid, []) for cid in customer_ids]

    async def _load_inventories(self, ids: Sequence[int]) -> list[InventoryType | None]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Inventory).where(Inventory.inventory_id.in_(ids))
            )
            mapping = {
                i.inventory_id: _inventory_to_type(i) for i in result.scalars().all()
            }
        return [mapping.get(id_) for id_ in ids]

    async def _load_payments_by_rental_id(
        self, rental_ids: Sequence[int]
    ) -> list[list[PaymentType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Payment).where(Payment.rental_id.in_(rental_ids))
            )
            payments = result.scalars().all()
        mapping: dict[int, list[PaymentType]] = defaultdict(list)
        for p in payments:
            mapping[p.rental_id].append(_payment_to_type(p))
        return [mapping.get(rid, []) for rid in rental_ids]

    # ── Reverse-relation batch functions ────────────────────────────────────

    async def _load_rentals(self, ids: Sequence[int]) -> list[RentalType | None]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Rental).where(Rental.rental_id.in_(ids))
            )
            mapping = {r.rental_id: _rental_to_type(r) for r in result.scalars().all()}
        return [mapping.get(id_) for id_ in ids]

    async def _load_films_by_actor_id(
        self, actor_ids: Sequence[int]
    ) -> list[list[FilmType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(FilmActor, Film)
                .join(Film, FilmActor.film_id == Film.film_id)
                .where(FilmActor.actor_id.in_(actor_ids))
            )
            rows = result.all()
        mapping: dict[int, list[FilmType]] = defaultdict(list)
        for film_actor, film in rows:
            mapping[film_actor.actor_id].append(_film_to_type(film))
        return [mapping.get(aid, []) for aid in actor_ids]

    async def _load_films_by_category_id(
        self, category_ids: Sequence[int]
    ) -> list[list[FilmType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(FilmCategory, Film)
                .join(Film, FilmCategory.film_id == Film.film_id)
                .where(FilmCategory.category_id.in_(category_ids))
            )
            rows = result.all()
        mapping: dict[int, list[FilmType]] = defaultdict(list)
        for film_cat, film in rows:
            mapping[film_cat.category_id].append(_film_to_type(film))
        return [mapping.get(cid, []) for cid in category_ids]

    async def _load_films_by_language_id(
        self, language_ids: Sequence[int]
    ) -> list[list[FilmType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Film).where(Film.language_id.in_(language_ids))
            )
            films = result.scalars().all()
        mapping: dict[int, list[FilmType]] = defaultdict(list)
        for f in films:
            mapping[f.language_id].append(_film_to_type(f))
        return [mapping.get(lid, []) for lid in language_ids]

    async def _load_inventories_by_film_id(
        self, film_ids: Sequence[int]
    ) -> list[list[InventoryType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Inventory).where(Inventory.film_id.in_(film_ids))
            )
            inventories = result.scalars().all()
        mapping: dict[int, list[InventoryType]] = defaultdict(list)
        for i in inventories:
            mapping[i.film_id].append(_inventory_to_type(i))
        return [mapping.get(fid, []) for fid in film_ids]

    async def _load_rentals_by_inventory_id(
        self, inventory_ids: Sequence[int]
    ) -> list[list[RentalType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Rental).where(Rental.inventory_id.in_(inventory_ids))
            )
            rentals = result.scalars().all()
        mapping: dict[int, list[RentalType]] = defaultdict(list)
        for r in rentals:
            mapping[r.inventory_id].append(_rental_to_type(r))
        return [mapping.get(iid, []) for iid in inventory_ids]

    async def _load_payments_by_customer_id(
        self, customer_ids: Sequence[int]
    ) -> list[list[PaymentType]]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(Payment).where(Payment.customer_id.in_(customer_ids))
            )
            payments = result.scalars().all()
        mapping: dict[int, list[PaymentType]] = defaultdict(list)
        for p in payments:
            mapping[p.customer_id].append(_payment_to_type(p))
        return [mapping.get(cid, []) for cid in customer_ids]
