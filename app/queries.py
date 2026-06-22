from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import User


def _paginate(stmt, page: int, page_size: int):
    offset = (page - 1) * page_size
    return stmt.offset(offset).limit(page_size)


def get_all_users(db: Session, page: int = 1, page_size: int = 20) -> list[User]:
    stmt = _paginate(select(User).order_by(User.created_at.desc()), page, page_size)
    return list(db.scalars(stmt))


def get_users_by_status(
    db: Session, status: str, page: int = 1, page_size: int = 20
) -> list[User]:
    stmt = _paginate(
        select(User).where(User.status == status).order_by(User.created_at.desc()),
        page,
        page_size,
    )
    return list(db.scalars(stmt))


def get_users_by_date_range(
    db: Session,
    date_from: datetime,
    date_to: datetime,
    page: int = 1,
    page_size: int = 20,
) -> list[User]:
    stmt = _paginate(
        select(User)
        .where(User.created_at >= date_from, User.created_at <= date_to)
        .order_by(User.created_at.desc()),
        page,
        page_size,
    )
    return list(db.scalars(stmt))


def get_users_by_country(
    db: Session, country: str, page: int = 1, page_size: int = 20
) -> list[User]:
    stmt = _paginate(
        select(User)
        .where(User.country == country)
        .order_by(User.created_at.desc()),
        page,
        page_size,
    )
    return list(db.scalars(stmt))


def search_users_by_name(
    db: Session, name_search: str, page: int = 1, page_size: int = 20
) -> list[User]:
    # LIKE with a parametrized value — no string concatenation with user input
    pattern = f"%{name_search}%"
    stmt = _paginate(
        select(User)
        .where(User.name.like(pattern))
        .order_by(User.created_at.desc()),
        page,
        page_size,
    )
    return list(db.scalars(stmt))
