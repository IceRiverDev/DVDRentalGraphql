from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry


@strawberry.type
class CountryType:
    country_id: int
    country: str
    last_update: datetime


@strawberry.type
class CityType:
    city_id: int
    city: str
    country_id: int
    last_update: datetime


@strawberry.type
class AddressType:
    address_id: int
    address: str
    address2: Optional[str]
    district: str
    city_id: int
    postal_code: Optional[str]
    phone: str
    last_update: datetime
