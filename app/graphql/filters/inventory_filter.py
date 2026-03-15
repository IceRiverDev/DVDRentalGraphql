from __future__ import annotations

from typing import List, Optional

import strawberry

from app.graphql.filters.shared import IntFilter
from app.graphql.types.common import PageInfo
from app.graphql.types.transactions import InventoryType


@strawberry.input
class InventoryFilter:
    inventory_id: Optional[IntFilter] = None
    film_id: Optional[IntFilter] = None
    store_id: Optional[IntFilter] = None
    is_available: Optional[bool] = None


@strawberry.type
class InventoryConnection:
    items: List[InventoryType]
    page_info: PageInfo
