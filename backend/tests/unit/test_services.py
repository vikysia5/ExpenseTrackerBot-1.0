# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal


@pytest.fixture(autouse=True)
def mock_supabase_client():
    mock_client = MagicMock()
    with patch('src.core.database.get_supabase_admin', return_value=mock_client), \
         patch('src.core.database.get_supabase', return_value=mock_client):
        yield mock_client


class TestTransactionFacade:

    @pytest.mark.asyncio
    async def test_get_transactions_returns_sorted_list(self, mock_supabase_client):
        from src.services.services import TransactionFacade

        fake_txs = [
            {'type': 'income',  'amount': '100',
             'transaction_date': '2024-04-01', 'category': None},
            {'type': 'expense', 'amount': '50',
             'transaction_date': '2024-04-02', 'category': None},
        ]

        with patch('src.repositories.repositories.TransactionRepository.get_all',
                   new=AsyncMock(return_value=fake_txs)):
            facade = TransactionFacade()
            result = await facade.get_transactions('user-1')

        assert result['total'] == 2
        assert result['income_total'] == 100.0
        assert result['expense_total'] == 50.0
        assert result['balance'] == 50.0

    @pytest.mark.asyncio
    async def test_create_transaction_calls_repository(self, mock_supabase_client):
        from src.services.services import TransactionFacade
        from src.models.schemas import TransactionCreate

        fake_tx = {'id': 'tx-1', 'type': 'income',
                   'amount': '100', 'category': None}
        repo_mock = AsyncMock()
        repo_mock.create = AsyncMock(return_value=fake_tx)
        notifier_mock = MagicMock()
        notifier_mock.send = AsyncMock(return_value=True)

        with patch('src.services.services.TransactionRepository',
                   return_value=repo_mock), \
             patch('src.services.services.NotifierFactory.create',
                   return_value=notifier_mock), \
             patch('src.services.services.event_bus.publish',
                   new=AsyncMock()):
            facade = TransactionFacade()
            data = TransactionCreate(type='income', amount=Decimal('100'))
            result = await facade.create_transaction('u1', data)

        assert result['id'] == 'tx-1'
        repo_mock.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_transactions_empty_returns_zero_balance(self, mock_supabase_client):
        from src.services.services import TransactionFacade

        with patch('src.repositories.repositories.TransactionRepository.get_all',
                   new=AsyncMock(return_value=[])):
            facade = TransactionFacade()
            result = await facade.get_transactions('user-empty')

        assert result['total'] == 0
        assert result['balance'] == 0

    @pytest.mark.asyncio
    async def test_delete_transaction_returns_true(self, mock_supabase_client):
        from src.services.services import TransactionFacade

        repo_mock = AsyncMock()
        repo_mock.delete = AsyncMock(return_value=True)

        with patch('src.services.services.TransactionRepository',
                   return_value=repo_mock), \
             patch('src.services.services.event_bus.publish',
                   new=AsyncMock()):
            facade = TransactionFacade()
            result = await facade.delete_transaction('tx-1', 'user-1')

        assert result is True
        repo_mock.delete.assert_awaited_once_with('tx-1', 'user-1')

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, mock_supabase_client):
        from src.services.services import TransactionFacade

        repo_mock = AsyncMock()
        repo_mock.delete = AsyncMock(return_value=False)

        with patch('src.services.services.TransactionRepository',
                   return_value=repo_mock), \
             patch('src.services.services.event_bus.publish',
                   new=AsyncMock()):
            facade = TransactionFacade()
            result = await facade.delete_transaction('no-id', 'user-1')

        assert result is False
