# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from src.services.services import TransactionFacade

class TestTransactionFacade:
    @pytest.mark.asyncio
    async def test_get_transactions_returns_sorted_list(self):
        with patch('src.services.services.TransactionRepository.get_all',
                   new=AsyncMock(return_value=[
                     {'type':'income','amount':'100',
                      'transaction_date':'2024-04-01'},
                     {'type':'expense','amount':'50',
                      'transaction_date':'2024-04-02'}])):
            from src.services.services import TransactionFacade
            facade = TransactionFacade()
            result = await facade.get_transactions('user-1')
            assert result['total'] == 2
            assert result['income_total'] == 100.0
            assert result['expense_total'] == 50.0
            assert result['balance'] == 50.0

    @pytest.mark.asyncio
    async def test_create_transaction_calls_repository(self):
        repo_create = AsyncMock(return_value={
            'id': 'tx-1', 'type': 'income', 'amount': '100'
        })
        notifier = AsyncMock()
        notifier.send = AsyncMock(return_value=True)

        with patch('src.services.services.TransactionRepository.create', new=repo_create), \
             patch('src.services.services.NotifierFactory.create', return_value=notifier), \
             patch('src.services.services.event_bus.publish', new=AsyncMock()):
            from src.services.services import TransactionFacade
            from src.models.schemas import TransactionCreate
            facade = TransactionFacade()
            data = TransactionCreate(type='income', amount=Decimal('100'))
            result = await facade.create_transaction('u1', data)

            assert result['id'] == 'tx-1'
            repo_create.assert_awaited_once()
