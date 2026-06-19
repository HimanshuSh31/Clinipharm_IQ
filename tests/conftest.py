"""
tests/conftest.py — Shared pytest fixtures for the Pharmacy Management System.

Strategy:
  - Patch database.get_connection to return a fresh in-memory SQLite connection
    for every test function.  This completely bypasses the @st.cache_resource
    decorator, so no running Streamlit server is required.
  - autouse=True ensures every test in the suite runs against a clean DB.
"""

import sqlite3
import pytest
from unittest.mock import patch


@pytest.fixture
def db_conn():
    """Create a fresh in-memory SQLite connection with FK enforcement."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@pytest.fixture(autouse=True)
def setup_db(db_conn):
    """
    For every test:
      1. Patch database.get_connection to return the in-memory connection.
      2. Run create_all_tables() so schema is ready.
      3. Yield the connection for tests that need direct DB access.
      4. Close the connection after the test.
    """
    with patch("database.get_connection", return_value=db_conn):
        import database
        database.create_all_tables()
        yield db_conn
    db_conn.close()
