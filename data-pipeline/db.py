"""Database connection module for data pipeline."""

import psycopg2
from psycopg2 import pool
import config
from typing import Optional

class DatabaseConnection:
    _connection_pool = None

    @classmethod
    def init_pool(cls, min_conn: int = 1, max_conn: int = 10):
        """Initialize connection pool."""
        if cls._connection_pool is None:
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                host=config.DB_HOST,
                port=config.DB_PORT,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD
            )

    @classmethod
    def get_connection(cls):
        """Get connection from pool."""
        if cls._connection_pool is None:
            cls.init_pool()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, conn):
        """Return connection to pool."""
        if cls._connection_pool is not None:
            cls._connection_pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Close all connections in pool."""
        if cls._connection_pool is not None:
            cls._connection_pool.closeall()
            cls._connection_pool = None

def log_ingestion(db_conn, data_source: str, records_ingested: int, status: str, error_msg: str = None):
    """Log data ingestion event."""
    try:
        cursor = db_conn.cursor()
        cursor.execute(
            '''
            INSERT INTO ingestion_logs (data_source, records_ingested, status, error_message)
            VALUES (%s, %s, %s, %s)
            ''',
            (data_source, records_ingested, status, error_msg)
        )
        db_conn.commit()
    except psycopg2.Error as e:
        print(f"Error logging ingestion: {e}")
        db_conn.rollback()
