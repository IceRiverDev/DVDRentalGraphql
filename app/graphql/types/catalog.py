from __future__ import annotations

from datetime import datetime

import strawberry


@strawberry.type
class LanguageType:
    language_id: int
    name: str
    last_update: datetime


@strawberry.type
class CategoryType:
    category_id: int
    name: str
    last_update: datetime


@strawberry.type
class ActorType:
    actor_id: int
    first_name: str
    last_name: str
    last_update: datetime
