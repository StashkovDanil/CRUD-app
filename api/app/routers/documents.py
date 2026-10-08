from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from ..db import get_conn
from ..schemas import DocumentDetail, DocumentIn, DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])

LIST_SELECT = """
    SELECT d.id, d.doc_number, d.doc_type, d.warehouse_id, w.name AS warehouse_name,
           d.supplier_id, s.name AS supplier_name, d.status, d.created_at, d.comment
    FROM documents d
    JOIN warehouses w ON w.id = d.warehouse_id
    LEFT JOIN suppliers s ON s.id = d.supplier_id
"""

ITEMS_SELECT = """
    SELECT di.id, di.product_id, p.name AS product_name, di.quantity, di.price
    FROM document_items di
    JOIN products p ON p.id = di.product_id
    WHERE di.document_id = %s
    ORDER BY di.id
"""


def _document_detail(conn: Connection, doc_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(LIST_SELECT + " WHERE d.id = %s", (doc_id,))
        doc = cur.fetchone()
        if doc is None:
            raise HTTPException(status_code=404, detail="Документ не найден")
        cur.execute(ITEMS_SELECT, (doc_id,))
        doc["items"] = cur.fetchall()
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(
    status: Optional[str] = Query(None),
    warehouse_id: Optional[int] = Query(None),
    conn: Connection = Depends(get_conn),
):
    query = LIST_SELECT
    conditions: list = []
    params: list = []
    if status:
        conditions.append("d.status = %s::document_status")
        params.append(status)
    if warehouse_id is not None:
        conditions.append("d.warehouse_id = %s")
        params.append(warehouse_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY d.created_at DESC"
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.post("", response_model=DocumentDetail, status_code=201)
def create_document(payload: DocumentIn, conn: Connection = Depends(get_conn)):
    """Создаёт документ-черновик вместе со всеми позициями одной транзакцией."""
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM warehouses WHERE id = %s", (payload.warehouse_id,))
            if cur.fetchone() is None:
                raise HTTPException(status_code=400, detail="Склад не найден")

            if payload.supplier_id is not None:
                cur.execute("SELECT id FROM suppliers WHERE id = %s", (payload.supplier_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=400, detail="Поставщик не найден")

            cur.execute(
                """
                INSERT INTO documents (doc_number, doc_type, warehouse_id, supplier_id, comment)
                VALUES (%s, %s::document_type, %s, %s, %s)
                RETURNING id
                """,
                (payload.doc_number, payload.doc_type, payload.warehouse_id,
                 payload.supplier_id, payload.comment),
            )
            doc_id = cur.fetchone()["id"]

            for item in payload.items:
                cur.execute("SELECT id FROM products WHERE id = %s", (item.product_id,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=400, detail=f"Товар id={item.product_id} не найден")
                cur.execute(
                    """
                    INSERT INTO document_items (document_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (doc_id, item.product_id, item.quantity, item.price),
                )
    return _document_detail(conn, doc_id)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, conn: Connection = Depends(get_conn)):
    return _document_detail(conn, document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, conn: Connection = Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM documents WHERE id = %s", (document_id,))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Документ не найден")
        if row["status"] != "DRAFT":
            raise HTTPException(status_code=409, detail="Удалять можно только черновик")
        cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))


@router.post("/{document_id}/post", response_model=DocumentDetail)
def post_document(document_id: int, conn: Connection = Depends(get_conn)):
    """
    Проведение документа — ключевая бизнес-операция склада.
    В одной транзакции:
      1) блокируем документ (FOR UPDATE), проверяем, что это черновик;
      2) для расхода — проверяем достаточность остатка по каждой позиции;
      3) обновляем остатки (INSERT ... ON CONFLICT ... DO UPDATE);
      4) переводим документ в статус POSTED.
    """
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE id = %s FOR UPDATE", (document_id,))
            doc = cur.fetchone()
            if doc is None:
                raise HTTPException(status_code=404, detail="Документ не найден")
            if doc["status"] != "DRAFT":
                raise HTTPException(status_code=409, detail="Проводить можно только черновик")

            cur.execute(ITEMS_SELECT, (document_id,))
            items = cur.fetchall()
            if not items:
                raise HTTPException(status_code=400, detail="В документе нет позиций")

            sign = 1 if doc["doc_type"] == "IN" else -1

            if doc["doc_type"] == "OUT":
                for item in items:
                    cur.execute(
                        "SELECT quantity FROM stock WHERE product_id = %s AND warehouse_id = %s FOR UPDATE",
                        (item["product_id"], doc["warehouse_id"]),
                    )
                    stock_row = cur.fetchone()
                    available = stock_row["quantity"] if stock_row else 0
                    if available < item["quantity"]:
                        raise HTTPException(
                            status_code=409,
                            detail=(
                                f"Недостаточно остатка «{item['product_name']}»: "
                                f"доступно {available}, требуется {item['quantity']}"
                            ),
                        )

            for item in items:
                cur.execute(
                    """
                    INSERT INTO stock (product_id, warehouse_id, quantity, updated_at)
                    VALUES (%s, %s, %s, now())
                    ON CONFLICT (product_id, warehouse_id)
                    DO UPDATE SET quantity = stock.quantity + EXCLUDED.quantity, updated_at = now()
                    """,
                    (item["product_id"], doc["warehouse_id"], sign * item["quantity"]),
                )

            cur.execute("UPDATE documents SET status = 'POSTED' WHERE id = %s", (document_id,))
    return _document_detail(conn, document_id)