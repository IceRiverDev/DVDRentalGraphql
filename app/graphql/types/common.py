from __future__ import annotations

import strawberry


@strawberry.type
class PageInfo:
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
