from datetime import datetime
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    status: str
    country: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryParams(BaseModel):
    filter_type: str  # all | status | date_range | country | name_search
    status: str | None = None
    country: str | None = None
    name_search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    page_size: int = 20
