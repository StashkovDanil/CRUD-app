import psycopg.errors
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routers.documents import router as documents_router
from .routers.products import router as products_router
from .routers.reference_data import categories_router, suppliers_router, warehouses_router
from .routers.stock import router as stock_router

app = FastAPI(
    title="Warehouse CRUD API",
    description="Учебное API для системы складского учёта (API First, честный SQL)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories_router)
app.include_router(suppliers_router)
app.include_router(warehouses_router)
app.include_router(products_router)
app.include_router(stock_router)
app.include_router(documents_router)


@app.exception_handler(psycopg.errors.UniqueViolation)
def handle_unique_violation(request: Request, exc: psycopg.errors.UniqueViolation):
    return JSONResponse(status_code=409, content={"detail": "Запись с такими данными уже существует"})


@app.exception_handler(psycopg.errors.ForeignKeyViolation)
def handle_fk_violation(request: Request, exc: psycopg.errors.ForeignKeyViolation):
    return JSONResponse(
        status_code=409,
        content={"detail": "Запись используется в связанных данных и не может быть изменена/удалена"},
    )


@app.exception_handler(psycopg.errors.CheckViolation)
def handle_check_violation(request: Request, exc: psycopg.errors.CheckViolation):
    return JSONResponse(status_code=422, content={"detail": "Нарушено ограничение целостности данных"})


@app.exception_handler(psycopg.errors.InvalidTextRepresentation)
def handle_invalid_enum(request: Request, exc: psycopg.errors.InvalidTextRepresentation):
    return JSONResponse(status_code=400, content={"detail": "Некорректное значение поля"})


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}