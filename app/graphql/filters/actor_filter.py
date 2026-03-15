from __future__ import annotations

import enum
from typing import List, Optional

import strawberry

from app.graphql.filters.shared import IntFilter, SortDirection, StringFilter
from app.graphql.types.catalog import ActorType
from app.graphql.types.common import PageInfo


@strawberry.enum
class ActorSortField(enum.Enum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ACTOR_ID = "actor_id"


@strawberry.input
class ActorFilter:
    actor_id: Optional[IntFilter] = None
    name: Optional[StringFilter] = None
    first_name: Optional[StringFilter] = None
    last_name: Optional[StringFilter] = None
    film_id: Optional[IntFilter] = None


@strawberry.input
class ActorSort:
    field: ActorSortField = ActorSortField.LAST_NAME
    direction: SortDirection = SortDirection.ASC


@strawberry.type
class ActorConnection:
    items: List[ActorType]
    page_info: PageInfo
