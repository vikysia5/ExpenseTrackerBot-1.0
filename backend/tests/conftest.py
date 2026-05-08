# tests/conftest.py
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_supabase():
    """
    Mock-клієнт Supabase для інтеграційних тестів.
    Замінює реальне підключення до БД — тести працюють
    без мережі та реальних даних.
    """
    client = MagicMock()

    # ── INSERT ────────────────────────────────────────────────
    client.table.return_value.insert.return_value \
        .execute.return_value.data = [
            {'id': 'test-id', 'type': 'income',
             'amount': '100', 'user_id': 'user-1'}
        ]

    # ── SELECT (список) ───────────────────────────────────────
    client.table.return_value.select.return_value \
        .eq.return_value.execute.return_value.data = [
            {'id': 'test-id', 'type': 'income', 'amount': '100'}
        ]

    # ── SELECT (single) ───────────────────────────────────────
    client.table.return_value.select.return_value \
        .eq.return_value.eq.return_value \
        .single.return_value.execute.return_value.data = {
            'id': 'test-id', 'type': 'income', 'amount': '100'
        }

    # ── DELETE ────────────────────────────────────────────────
    client.table.return_value.delete.return_value \
        .eq.return_value.eq.return_value \
        .execute.return_value.data = [{'id': 'test-id'}]

    # ── UPDATE ────────────────────────────────────────────────
    client.table.return_value.update.return_value \
        .eq.return_value.eq.return_value \
        .execute.return_value.data = [
            {'id': 'test-id', 'type': 'income', 'amount': '250'}
        ]

    return client