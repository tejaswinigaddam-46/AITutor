import psycopg2
from psycopg2 import pool
from pgvector.psycopg2 import register_vector
from contextlib import contextmanager
from app.core.config import settings

class DatabaseSession:
    _pool = None

    @classmethod
    def get_pool(cls):
        if cls._pool is None:
            try:
                # We use ThreadedConnectionPool for thread-safety in FastAPI
                cls._pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=settings.DB_MIN_CONNECTIONS,
                    maxconn=settings.DB_MAX_CONNECTIONS,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD
                )
                print("Database connection pool created successfully")
            except Exception as e:
                print(f"Error creating database connection pool: {e}")
                raise e
        return cls._pool

    @classmethod
    @contextmanager
    def get_connection(cls):
        pool = cls.get_pool()
        conn = pool.getconn()
        try:
            # Register pgvector type for this connection
            register_vector(conn)
            yield conn
        finally:
            pool.putconn(conn)

    @classmethod
    def close_all_connections(cls):
        if cls._pool:
            cls._pool.closeall()
            print("All database connections closed")

db_session = DatabaseSession()
