from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL

# autocommit=True — каждый одиночный запрос коммитится сразу;
# для многошаговых операций (см. routers/documents.py) явно открываем
# транзакцию через `with conn.transaction():`.
# row_factory=dict_row — cursor.fetchone()/fetchall() сразу возвращают dict,
# совместимый с pydantic response_model.
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=10,
    open=True,
    kwargs={"autocommit": True, "row_factory": dict_row},
)


def get_conn():
    """FastAPI-зависимость: выдаёт соединение из пула на время запроса."""
    with pool.connection() as conn:
        yield conn