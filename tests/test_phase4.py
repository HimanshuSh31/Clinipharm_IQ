"""
tests/test_phase4.py — Unit tests for Phase 4 features (Analytics & Audit Logs).
"""

import pytest
from unittest.mock import MagicMock, patch
import database


def test_db_wrapper_param_translation():
    """
    Verify that DbCursorWrapper correctly translates SQLite '?' placeholders
    to PostgreSQL '%s' placeholders when in postgres mode.
    """
    mock_cursor = MagicMock()
    
    # 1. Test postgres mode (should translate)
    pg_wrapper = database.DbCursorWrapper(mock_cursor, is_postgres=True)
    pg_wrapper.execute("SELECT * FROM Drugs WHERE D_id = ? AND D_Qty > ?", ("DRUG1", 5))
    mock_cursor.execute.assert_called_with(
        "SELECT * FROM Drugs WHERE D_id = %s AND D_Qty > %s",
        ("DRUG1", 5)
    )
    
    # 2. Test sqlite mode (should NOT translate)
    mock_cursor.reset_mock()
    sqlite_wrapper = database.DbCursorWrapper(mock_cursor, is_postgres=False)
    sqlite_wrapper.execute("SELECT * FROM Drugs WHERE D_id = ? AND D_Qty > ?", ("DRUG1", 5))
    mock_cursor.execute.assert_called_with(
        "SELECT * FROM Drugs WHERE D_id = ? AND D_Qty > ?",
        ("DRUG1", 5)
    )


def test_audit_logging():
    """
    Verify that state-changing admin operations correctly write to
    the AuditLogs table and that audit_log_view_all retrieves them.
    """
    # Create a fresh drug
    drug_id = "TEST-AUD-1"
    ok = database.drug_add_data(
        name="Test Audit Drug",
        expdate="2027-12-31",
        use="For testing audit logs",
        qty=100,
        drug_id=drug_id,
        price=12.5,
        category="Supplement"
    )
    assert ok is True

    # Retrieve audit logs
    logs = database.audit_log_view_all()
    assert len(logs) >= 1
    
    # The newest log should be our Drug Added log
    latest_log = logs[0]
    # Columns: (AL_id, AL_Timestamp, AL_User, AL_Action, AL_Details)
    assert latest_log[2] == "System"  # No active session in pytest
    assert latest_log[3] == "Drug Added"
    assert drug_id in latest_log[4]
    assert "Test Audit Drug" in latest_log[4]

    # Clean up the drug
    deleted, msg = database.drug_delete(drug_id)
    assert deleted is True

    # Verify a new log was written for deletion
    logs = database.audit_log_view_all()
    assert len(logs) >= 2
    deletion_log = logs[0]
    assert deletion_log[3] == "Drug Deleted"
    assert drug_id in deletion_log[4]


def test_audit_logging_automatic_user_resolution():
    """
    Verify that audit_log_write automatically resolves the active admin
    from Streamlit's st.session_state if not explicitly provided.
    """
    mock_session_state = MagicMock()
    mock_session_state.get.side_effect = lambda key, default=None: {
        "logged_in": True,
        "username": "admin_audit_test@pharma.com"
    }.get(key, default)
    
    # We patch st.session_state to simulate an active logged-in admin session
    with patch("streamlit.session_state", mock_session_state), \
         patch("streamlit.cache_resource", lambda x: x):
        
        database.audit_log_write(
            action="Test Auto User",
            details="Verifying session state username extraction",
            user_email=None,
            commit=True
        )
        
        # Verify the log was written with the simulated user
        logs = database.audit_log_view_all()
        assert len(logs) >= 1
        latest_log = logs[0]
        assert latest_log[2] == "admin_audit_test@pharma.com"
        assert latest_log[3] == "Test Auto User"
        assert "Verifying session state username" in latest_log[4]


def test_analytics_sales_data_query():
    """
    Verify that analytics_get_raw_sales_data executes successfully.
    """
    data = database.analytics_get_raw_sales_data()
    # It should return a list of tuples (can be empty if no orders exist, but query must not crash)
    assert isinstance(data, list)
    if len(data) > 0:
        first_row = data[0]
        # Should have 6 elements: (O_Timestamp, quantity, unit_price, D_name, O_Status, D_Category)
        assert len(first_row) == 6
