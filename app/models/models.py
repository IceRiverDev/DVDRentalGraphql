from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MpaaRating(enum.StrEnum):
    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"


class Country(Base):
    __tablename__ = "country"

    country_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    cities: Mapped[list[City]] = relationship("City", back_populates="country_rel")


class City(Base):
    __tablename__ = "city"

    city_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    country_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("country.country_id"), nullable=False
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    country_rel: Mapped[Country] = relationship("Country", back_populates="cities")
    addresses: Mapped[list[Address]] = relationship(
        "Address", back_populates="city_rel"
    )


class Address(Base):
    __tablename__ = "address"

    address_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(50), nullable=False)
    address2: Mapped[str | None] = mapped_column(String(50))
    district: Mapped[str] = mapped_column(String(20), nullable=False)
    city_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("city.city_id"), nullable=False
    )
    postal_code: Mapped[str | None] = mapped_column(String(10))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    city_rel: Mapped[City] = relationship("City", back_populates="addresses")
    customers: Mapped[list[Customer]] = relationship(
        "Customer", back_populates="address_rel"
    )
    staff_members: Mapped[list[Staff]] = relationship(
        "Staff", back_populates="address_rel"
    )
    stores: Mapped[list[Store]] = relationship("Store", back_populates="address_rel")


class Language(Base):
    __tablename__ = "language"

    language_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    films: Mapped[list[Film]] = relationship("Film", back_populates="language_rel")


class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    film_categories: Mapped[list[FilmCategory]] = relationship(
        "FilmCategory", back_populates="category_rel"
    )


class Actor(Base):
    __tablename__ = "actor"

    actor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(45), nullable=False)
    last_name: Mapped[str] = mapped_column(String(45), nullable=False)
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    film_actors: Mapped[list[FilmActor]] = relationship(
        "FilmActor", back_populates="actor_rel"
    )


class Film(Base):
    __tablename__ = "film"

    film_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(Integer)
    language_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("language.language_id"), nullable=False
    )
    rental_duration: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="3"
    )
    rental_rate: Mapped[Decimal] = mapped_column(
        Numeric(4, 2), nullable=False, server_default="4.99"
    )
    length: Mapped[int | None] = mapped_column(SmallInteger)
    replacement_cost: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, server_default="19.99"
    )
    rating: Mapped[MpaaRating | None] = mapped_column(
        SAEnum(
            MpaaRating,
            name="mpaa_rating",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        server_default="G",
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    special_features: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    fulltext: Mapped[str] = mapped_column(TSVECTOR, nullable=False)

    language_rel: Mapped[Language] = relationship("Language", back_populates="films")
    film_actors: Mapped[list[FilmActor]] = relationship(
        "FilmActor", back_populates="film_rel"
    )
    film_categories: Mapped[list[FilmCategory]] = relationship(
        "FilmCategory", back_populates="film_rel"
    )
    inventory_items: Mapped[list[Inventory]] = relationship(
        "Inventory", back_populates="film_rel"
    )


class FilmActor(Base):
    __tablename__ = "film_actor"

    actor_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("actor.actor_id"), primary_key=True
    )
    film_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("film.film_id"), primary_key=True
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    actor_rel: Mapped[Actor] = relationship("Actor", back_populates="film_actors")
    film_rel: Mapped[Film] = relationship("Film", back_populates="film_actors")


class FilmCategory(Base):
    __tablename__ = "film_category"

    film_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("film.film_id"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("category.category_id"), primary_key=True
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    film_rel: Mapped[Film] = relationship("Film", back_populates="film_categories")
    category_rel: Mapped[Category] = relationship(
        "Category", back_populates="film_categories"
    )


class Customer(Base):
    __tablename__ = "customer"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    first_name: Mapped[str] = mapped_column(String(45), nullable=False)
    last_name: Mapped[str] = mapped_column(String(45), nullable=False)
    email: Mapped[str | None] = mapped_column(String(50))
    address_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("address.address_id"), nullable=False
    )
    activebool: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    create_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.now()
    )
    last_update: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now()
    )
    active: Mapped[int | None] = mapped_column(Integer)

    address_rel: Mapped[Address] = relationship("Address", back_populates="customers")
    rentals: Mapped[list[Rental]] = relationship(
        "Rental", back_populates="customer_rel"
    )
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="customer_rel"
    )


class Staff(Base):
    __tablename__ = "staff"

    staff_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(45), nullable=False)
    last_name: Mapped[str] = mapped_column(String(45), nullable=False)
    address_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("address.address_id"), nullable=False
    )
    email: Mapped[str | None] = mapped_column(String(50))
    store_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    username: Mapped[str] = mapped_column(String(16), nullable=False)
    password: Mapped[str | None] = mapped_column(String(40))
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    picture: Mapped[bytes | None] = mapped_column(LargeBinary)

    address_rel: Mapped[Address] = relationship(
        "Address", back_populates="staff_members"
    )
    rentals: Mapped[list[Rental]] = relationship("Rental", back_populates="staff_rel")
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="staff_rel"
    )
    managed_stores: Mapped[list[Store]] = relationship(
        "Store", back_populates="manager_rel", foreign_keys="Store.manager_staff_id"
    )


class Store(Base):
    __tablename__ = "store"

    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manager_staff_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("staff.staff_id"), nullable=False
    )
    address_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("address.address_id"), nullable=False
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    manager_rel: Mapped[Staff] = relationship(
        "Staff", back_populates="managed_stores", foreign_keys=[manager_staff_id]
    )
    address_rel: Mapped[Address] = relationship("Address", back_populates="stores")
    inventory_items: Mapped[list[Inventory]] = relationship(
        "Inventory", back_populates="store_rel"
    )


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    film_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("film.film_id"), nullable=False
    )
    store_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("store.store_id"), nullable=False
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    film_rel: Mapped[Film] = relationship("Film", back_populates="inventory_items")
    store_rel: Mapped[Store] = relationship("Store", back_populates="inventory_items")
    rentals: Mapped[list[Rental]] = relationship(
        "Rental", back_populates="inventory_rel"
    )


class Rental(Base):
    __tablename__ = "rental"

    rental_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rental_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    inventory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory.inventory_id"), nullable=False
    )
    customer_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("customer.customer_id"), nullable=False
    )
    return_date: Mapped[datetime | None] = mapped_column(DateTime)
    staff_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("staff.staff_id"), nullable=False
    )
    last_update: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    inventory_rel: Mapped[Inventory] = relationship(
        "Inventory", back_populates="rentals"
    )
    customer_rel: Mapped[Customer] = relationship("Customer", back_populates="rentals")
    staff_rel: Mapped[Staff] = relationship("Staff", back_populates="rentals")
    payments: Mapped[list[Payment]] = relationship(
        "Payment", back_populates="rental_rel"
    )


class Payment(Base):
    __tablename__ = "payment"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("customer.customer_id"), nullable=False
    )
    staff_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("staff.staff_id"), nullable=False
    )
    rental_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rental.rental_id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    customer_rel: Mapped[Customer] = relationship("Customer", back_populates="payments")
    staff_rel: Mapped[Staff] = relationship("Staff", back_populates="payments")
    rental_rel: Mapped[Rental] = relationship("Rental", back_populates="payments")
