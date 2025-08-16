from contextlib import contextmanager
import os

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def configure_pool_connection(conn: psycopg.Connection) -> None:
    register_vector(conn)

conninfo = os.getenv(
    "DATABASE_URL",
    "dbname=edsearch user=postgres password=password host=localhost",
)
pool = ConnectionPool(
    conninfo=conninfo,
    open=True,
    configure=configure_pool_connection,
)


def get_pg_connection():
    conn = pool.getconn()
    register_vector(conn)
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SET hnsw.ef_search = 1000;")
    return conn, cur


@contextmanager
def pg_connection():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SET hnsw.ef_search = 1000;")
            try:
                yield conn, cur
            finally:
                conn.commit()


def create_tables(table_statements: list[str], drop: bool) -> None:
    conn = psycopg.connect(conninfo)
    cur = conn.cursor()
    
    if drop:
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
    register_vector(conn)
    for statement in table_statements:
        cur.execute(statement)  # pyright: ignore[reportArgumentType]
    conn.commit()
    cur.close()
    conn.close()
