"""
CRUD для простых справочников: категории, поставщики, склады.
Все запросы — параметризованный SQL (psycopg %s), никаких f-строк/format()
со значениями пользователя внутри SQL-текста -> инъекция исключена.
"""
from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from ..db import get_conn
from ..schemas import (
    CategoryIn,
    CategoryOut,
    SupplierIn,
    SupplierOut,
    WarehouseIn,
    WarehouseOut,
)

categories_router = APIRouter(prefix="/categories", tags=["categories"])
suppliers_router = APIRouter(prefix="/suppliers", tags=["suppliers"])
warehouses_router = APIRouter(prefix="/warehouses", tags=["warehouses"])


# ---------------------------------------------------------------- Категории
@categories_router.get("", response_model=list[CategoryOut])
def list_categories(conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, description FROM categories ORDER BY name")
        return cur.fetchall()


@categories_router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO categories (name, description) VALUES (%s, %s) "
            "RETURNING id, name, description",
            (payload.name, payload.description),
        )
        return cur.fetchone()


@categories_router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE categories SET name = %s, description = %s WHERE id = %s "
            "RETURNING id, name, description",
            (payload.name, payload.description, category_id),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return row


@categories_router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        deleted = cur.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Категория не найдена")


# --------------------------------------------------------------- Поставщики
@suppliers_router.get("", response_model=list[SupplierOut])
def list_suppliers(conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, contact_person, phone, email FROM suppliers ORDER BY name"
        )
        return cur.fetchall()


@suppliers_router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(payload: SupplierIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO suppliers (name, contact_person, phone, email)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, contact_person, phone, email
            """,
            (payload.name, payload.contact_person, payload.phone, payload.email),
        )
        return cur.fetchone()


@suppliers_router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, payload: SupplierIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE suppliers SET name = %s, contact_person = %s, phone = %s, email = %s
            WHERE id = %s
            RETURNING id, name, contact_person, phone, email
            """,
            (payload.name, payload.contact_person, payload.phone, payload.email, supplier_id),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    return row


@suppliers_router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
        deleted = cur.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Поставщик не найден")


# ------------------------------------------------------------------ Склады
@warehouses_router.get("", response_model=list[WarehouseOut])
def list_warehouses(conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, address FROM warehouses ORDER BY name")
        return cur.fetchall()


@warehouses_router.post("", response_model=WarehouseOut, status_code=201)
def create_warehouse(payload: WarehouseIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO warehouses (name, address) VALUES (%s, %s) "
            "RETURNING id, name, address",
            (payload.name, payload.address),
        )
        return cur.fetchone()


@warehouses_router.put("/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(warehouse_id: int, payload: WarehouseIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE warehouses SET name = %s, address = %s WHERE id = %s "
            "RETURNING id, name, address",
            (payload.name, payload.address, warehouse_id),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Склад не найден")
    return row


@warehouses_router.delete("/{warehouse_id}", status_code=204)
def delete_warehouse(warehouse_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM warehouses WHERE id = %s", (warehouse_id,))
        deleted = cur.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Склад не найден")