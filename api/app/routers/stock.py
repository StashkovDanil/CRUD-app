from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from ..db import get_conn
from ..schemas import StockAdjust, StockOut

router = APIRouter(prefix="/stock", tags=["stock"])

SELECT_STOCK = """
    SELECT s.id, s.product_id, p.name AS product_name,
           s.warehouse_id, w.name AS warehouse_name,
           s.quantity, s.updated_at
    FROM stock s
    JOIN products p ON p.id = s.product_id
    JOIN warehouses w ON w.id = s.warehouse_id
"""


@router.get("", response_model=list[StockOut])
def list_stock(warehouse_id: Optional[int] = Query(None), conn: Connection = Depends(get_conn)):
    query = SELECT_STOCK
    params: list = []
    if warehouse_id is not None:
        query += " WHERE s.warehouse_id = %s"
        params.append(warehouse_id)
    query += " ORDER BY w.name, p.name"
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.patch("/{stock_id}", response_model=StockOut)
def adjust_stock(stock_id: int, payload: StockAdjust, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE stock SET quantity = %s, updated_at = now() WHERE id = %s",
            (payload.quantity, stock_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Остаток не найден")
        cur.execute(SELECT_STOCK + " WHERE s.id = %s", (stock_id,))
        return cur.fetchone()