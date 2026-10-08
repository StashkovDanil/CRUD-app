from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from ..db import get_conn
from ..schemas import ProductIn, ProductOut, ProductWithCategory

router = APIRouter(prefix="/products", tags=["products"])

SELECT_WITH_CATEGORY = """
    SELECT p.id, p.sku, p.name, p.category_id, p.unit, p.price, p.description,
           c.name AS category_name
    FROM products p
    JOIN categories c ON c.id = p.category_id
"""


@router.get("", response_model=list[ProductWithCategory])
def list_products(category_id: Optional[int] = Query(None), conn: Connection = Depends(get_conn)):
    query = SELECT_WITH_CATEGORY
    params: list = []
    if category_id is not None:
        query += " WHERE p.category_id = %s"
        params.append(category_id)
    query += " ORDER BY p.name"
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE id = %s", (payload.category_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=400, detail="Категория не найдена")
        cur.execute(
            """
            INSERT INTO products (sku, name, category_id, unit, price, description)
            VALUES (%s, %s, %s, COALESCE(%s, 'шт'), %s, %s)
            RETURNING id, sku, name, category_id, unit, price, description
            """,
            (payload.sku, payload.name, payload.category_id, payload.unit,
             payload.price, payload.description),
        )
        return cur.fetchone()


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductIn, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE id = %s", (payload.category_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=400, detail="Категория не найдена")
        cur.execute(
            """
            UPDATE products
            SET sku = %s, name = %s, category_id = %s,
                unit = COALESCE(%s, unit), price = %s, description = %s
            WHERE id = %s
            RETURNING id, sku, name, category_id, unit, price, description
            """,
            (payload.sku, payload.name, payload.category_id, payload.unit,
             payload.price, payload.description, product_id),
        )
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return row


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        deleted = cur.rowcount
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Товар не найден")