from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from prometheus_fastapi_instrumentator import Instrumentator

from db import get_db, check_db_connection, engine, Base
from sqlalchemy import text
from models import User
from schemas import UserOut, QueryParams
import queries
from seed import seed_if_empty

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        seed_if_empty(conn)
    yield


app = FastAPI(title="FastAPI MySQL App", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    db_ok = check_db_connection()
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "degraded", "db": db_ok},
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": [], "query_ran": False})


@app.post("/", response_class=HTMLResponse)
def index_query(
    request: Request,
    filter_type: str = Form(...),
    status: str = Form(None),
    country: str = Form(None),
    name_search: str = Form(None),
    date_from: str = Form(None),
    date_to: str = Form(None),
    page: int = Form(1),
    db: Session = Depends(get_db),
):
    params = QueryParams(
        filter_type=filter_type,
        status=status or None,
        country=country or None,
        name_search=name_search or None,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        page=page,
    )
    users = _run_query(params, db)
    results = [UserOut.model_validate(u).model_dump() for u in users]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "results": results, "query_ran": True, "filter_type": filter_type},
    )


@app.get("/api/query")
def api_query(
    filter_type: str = "all",
    status: str = None,
    country: str = None,
    name_search: str = None,
    date_from: str = None,
    date_to: str = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    params = QueryParams(
        filter_type=filter_type,
        status=status,
        country=country,
        name_search=name_search,
        date_from=datetime.fromisoformat(date_from) if date_from else None,
        date_to=datetime.fromisoformat(date_to) if date_to else None,
        page=page,
    )
    users = _run_query(params, db)
    return {"results": [UserOut.model_validate(u).model_dump() for u in users]}


@app.get("/users/add", response_class=HTMLResponse)
def add_user_form(request: Request):
    return templates.TemplateResponse("add_user.html", {"request": request})


@app.post("/users/add")
def add_user(
    name: str = Form(...),
    email: str = Form(...),
    status: str = Form(...),
    country: str = Form(...),
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    user = User(name=name, email=email, status=status, country=country, created_at=datetime.utcnow())
    db.add(user)
    db.commit()
    return RedirectResponse(url="/?added=1", status_code=303)


@app.get("/sql", response_class=HTMLResponse)
def sql_console(request: Request):
    return templates.TemplateResponse("sql_console.html", {"request": request})


@app.post("/sql", response_class=HTMLResponse)
def sql_run(request: Request, query: str = Form(...), db: Session = Depends(get_db)):
    try:
        result = db.execute(text(query))
        try:
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]
            return templates.TemplateResponse(
                "sql_console.html",
                {"request": request, "query": query, "columns": columns, "rows": rows, "error": None},
            )
        except Exception:
            db.commit()
            return templates.TemplateResponse(
                "sql_console.html",
                {"request": request, "query": query, "columns": [], "rows": [], "error": None, "info": "Query executed successfully (no rows returned)."},
            )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "sql_console.html",
            {"request": request, "query": query, "columns": [], "rows": [], "error": str(e)},
        )


def _run_query(params: QueryParams, db: Session) -> list[User]:
    match params.filter_type:
        case "status":
            return queries.get_users_by_status(db, params.status or "active", params.page)
        case "date_range":
            if params.date_from and params.date_to:
                return queries.get_users_by_date_range(db, params.date_from, params.date_to, params.page)
            return []
        case "country":
            return queries.get_users_by_country(db, params.country or "", params.page)
        case "name_search":
            return queries.search_users_by_name(db, params.name_search or "", params.page)
        case _:
            return queries.get_all_users(db, params.page)
