from __future__ import annotations

import enum
from typing import TYPE_CHECKING, List, Optional

import strawberry

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.orm import InstrumentedAttribute


@strawberry.enum
class SortDirection(enum.Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.enum
class MpaaRatingEnum(enum.StrEnum):
    G = "G"
    PG = "PG"
    PG13 = "PG-13"
    R = "R"
    NC17 = "NC-17"


# ── Scalar filter input types ──────────────────────────────────────────────────
# Each type supports a set of comparison operators as optional fields.
# Multiple operators on the same field are AND-ed together.


@strawberry.input(description="Filter operators for string columns")
class StringFilter:
    eq: Optional[str] = strawberry.field(default=None, description="Exact match")
    neq: Optional[str] = strawberry.field(default=None, description="Not equal")
    like: Optional[str] = strawberry.field(
        default=None, description="Case-sensitive LIKE (use % as wildcard)"
    )
    ilike: Optional[str] = strawberry.field(
        default=None, description="Case-insensitive LIKE (use % as wildcard)"
    )
    contains: Optional[str] = strawberry.field(
        default=None,
        description="Case-insensitive contains (shorthand for ilike %%value%%)",
    )
    starts_with: Optional[str] = strawberry.field(
        default=None, description="Case-insensitive starts with"
    )
    ends_with: Optional[str] = strawberry.field(
        default=None, description="Case-insensitive ends with"
    )
    in_: Optional[List[str]] = strawberry.field(
        default=None, description="Value is in list"
    )
    is_null: Optional[bool] = strawberry.field(
        default=None, description="True = IS NULL, False = IS NOT NULL"
    )


@strawberry.input(description="Filter operators for integer columns")
class IntFilter:
    eq: Optional[int] = strawberry.field(default=None, description="Equal")
    neq: Optional[int] = strawberry.field(default=None, description="Not equal")
    gt: Optional[int] = strawberry.field(default=None, description="Greater than")
    gte: Optional[int] = strawberry.field(
        default=None, description="Greater than or equal"
    )
    lt: Optional[int] = strawberry.field(default=None, description="Less than")
    lte: Optional[int] = strawberry.field(
        default=None, description="Less than or equal"
    )
    in_: Optional[List[int]] = strawberry.field(
        default=None, description="Value is in list"
    )
    is_null: Optional[bool] = strawberry.field(
        default=None, description="True = IS NULL, False = IS NOT NULL"
    )


@strawberry.input(description="Filter operators for float/decimal columns")
class FloatFilter:
    eq: Optional[float] = strawberry.field(default=None, description="Equal")
    neq: Optional[float] = strawberry.field(default=None, description="Not equal")
    gt: Optional[float] = strawberry.field(default=None, description="Greater than")
    gte: Optional[float] = strawberry.field(
        default=None, description="Greater than or equal"
    )
    lt: Optional[float] = strawberry.field(default=None, description="Less than")
    lte: Optional[float] = strawberry.field(
        default=None, description="Less than or equal"
    )
    is_null: Optional[bool] = strawberry.field(
        default=None, description="True = IS NULL, False = IS NOT NULL"
    )


@strawberry.input(description="Filter operators for datetime columns")
class DateTimeFilter:
    eq: Optional[str] = strawberry.field(default=None, description="Equal (ISO 8601)")
    gt: Optional[str] = strawberry.field(default=None, description="After (ISO 8601)")
    gte: Optional[str] = strawberry.field(
        default=None, description="After or equal (ISO 8601)"
    )
    lt: Optional[str] = strawberry.field(default=None, description="Before (ISO 8601)")
    lte: Optional[str] = strawberry.field(
        default=None, description="Before or equal (ISO 8601)"
    )
    is_null: Optional[bool] = strawberry.field(
        default=None, description="True = IS NULL, False = IS NOT NULL"
    )


@strawberry.input(description="Filter operators for date columns")
class DateFilter:
    eq: Optional[str] = strawberry.field(default=None, description="Equal (YYYY-MM-DD)")
    gt: Optional[str] = strawberry.field(default=None, description="After (YYYY-MM-DD)")
    gte: Optional[str] = strawberry.field(
        default=None, description="After or equal (YYYY-MM-DD)"
    )
    lt: Optional[str] = strawberry.field(
        default=None, description="Before (YYYY-MM-DD)"
    )
    lte: Optional[str] = strawberry.field(
        default=None, description="Before or equal (YYYY-MM-DD)"
    )


# ── Apply helpers ──────────────────────────────────────────────────────────────
# Each helper takes a SQLAlchemy query, a column, and a filter object,
# and returns the query with all active conditions applied.


def apply_string_filter(
    q: "Select", column: "InstrumentedAttribute", f: Optional[StringFilter]
) -> "Select":
    if f is None:
        return q
    if f.eq is not None:
        q = q.where(column == f.eq)
    if f.neq is not None:
        q = q.where(column != f.neq)
    if f.like is not None:
        q = q.where(column.like(f.like))
    if f.ilike is not None:
        q = q.where(column.ilike(f.ilike))
    if f.contains is not None:
        q = q.where(column.ilike(f"%{f.contains}%"))
    if f.starts_with is not None:
        q = q.where(column.ilike(f"{f.starts_with}%"))
    if f.ends_with is not None:
        q = q.where(column.ilike(f"%{f.ends_with}"))
    if f.in_ is not None:
        q = q.where(column.in_(f.in_))
    if f.is_null is not None:
        q = q.where(column.is_(None) if f.is_null else column.is_not(None))
    return q


def apply_int_filter(
    q: "Select", column: "InstrumentedAttribute", f: Optional[IntFilter]
) -> "Select":
    if f is None:
        return q
    if f.eq is not None:
        q = q.where(column == f.eq)
    if f.neq is not None:
        q = q.where(column != f.neq)
    if f.gt is not None:
        q = q.where(column > f.gt)
    if f.gte is not None:
        q = q.where(column >= f.gte)
    if f.lt is not None:
        q = q.where(column < f.lt)
    if f.lte is not None:
        q = q.where(column <= f.lte)
    if f.in_ is not None:
        q = q.where(column.in_(f.in_))
    if f.is_null is not None:
        q = q.where(column.is_(None) if f.is_null else column.is_not(None))
    return q


def apply_float_filter(
    q: "Select", column: "InstrumentedAttribute", f: Optional[FloatFilter]
) -> "Select":
    if f is None:
        return q
    if f.eq is not None:
        q = q.where(column == f.eq)
    if f.neq is not None:
        q = q.where(column != f.neq)
    if f.gt is not None:
        q = q.where(column > f.gt)
    if f.gte is not None:
        q = q.where(column >= f.gte)
    if f.lt is not None:
        q = q.where(column < f.lt)
    if f.lte is not None:
        q = q.where(column <= f.lte)
    if f.is_null is not None:
        q = q.where(column.is_(None) if f.is_null else column.is_not(None))
    return q


def apply_datetime_filter(
    q: "Select", column: "InstrumentedAttribute", f: Optional[DateTimeFilter]
) -> "Select":
    from datetime import datetime as dt

    if f is None:
        return q
    if f.eq is not None:
        q = q.where(column == dt.fromisoformat(f.eq))
    if f.gt is not None:
        q = q.where(column > dt.fromisoformat(f.gt))
    if f.gte is not None:
        q = q.where(column >= dt.fromisoformat(f.gte))
    if f.lt is not None:
        q = q.where(column < dt.fromisoformat(f.lt))
    if f.lte is not None:
        q = q.where(column <= dt.fromisoformat(f.lte))
    if f.is_null is not None:
        q = q.where(column.is_(None) if f.is_null else column.is_not(None))
    return q


def apply_date_filter(
    q: "Select", column: "InstrumentedAttribute", f: Optional[DateFilter]
) -> "Select":
    from datetime import date as d

    if f is None:
        return q
    if f.eq is not None:
        q = q.where(column == d.fromisoformat(f.eq))
    if f.gt is not None:
        q = q.where(column > d.fromisoformat(f.gt))
    if f.gte is not None:
        q = q.where(column >= d.fromisoformat(f.gte))
    if f.lt is not None:
        q = q.where(column < d.fromisoformat(f.lt))
    if f.lte is not None:
        q = q.where(column <= d.fromisoformat(f.lte))
    return q


@strawberry.input(description="Filter operators for Category")
class CategoryFilter:
    category_id: Optional[IntFilter] = strawberry.field(default=None)
    name: Optional[StringFilter] = strawberry.field(default=None)
