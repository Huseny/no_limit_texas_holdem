import psycopg2
from contextlib import contextmanager

DATABASE_URL = "postgresql://postgres@localhost:5432/poker"
# DATABASE_URL = "postgresql://pokeruser:pokerpassword@db/pokerdb"


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def truncate_tables():
    """Truncate all tables in the database."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE completed_hands")
            conn.commit()