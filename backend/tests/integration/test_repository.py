# tests/integration/test_repository.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ══════════════════════════════════════════════════════════════
# INTEGRATION TESTS — TransactionRepository + CategoryRepository
# Ізоляція від реального Supabase через mock-клієнт
# ══════════════════════════════════════════════════════════════


class TestTransactionRepositoryIntegration:

    # ──────────────────────────────────────────────────────────
    # TEST 1: create → повертає збережену транзакцію з id
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_create_and_retrieve(self, mock_supabase):
        """
        Інтеграційний: create() зберігає транзакцію,
        get_by_id() повертає той самий запис.
        """
        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import TransactionRepository
            repo = TransactionRepository()

            # Act: зберегти
            data = {
                'type': 'income',
                'amount': '100',
                'currency': 'USD',
                'payment_method': 'card',
                'transaction_date': '2024-04-01T10:00:00',
            }
            created = await repo.create('user-1', data)

            # Assert: запис повернувся з id
            assert created is not None
            assert created['id'] == 'test-id'
            assert created['type'] == 'income'
            assert created['amount'] == '100'

            # Act: знайти за id
            mock_supabase.table.return_value.select.return_value \
                .eq.return_value.eq.return_value \
                .single.return_value.execute.return_value.data = {
                    'id': 'test-id', 'type': 'income', 'amount': '100'
                }

            retrieved = await repo.get_by_id('test-id', 'user-1')

            # Assert: знайдений запис відповідає збереженому
            assert retrieved is not None
            assert retrieved['id'] == 'test-id'

    # ──────────────────────────────────────────────────────────
    # TEST 2: update → змінює поле amount
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_update_changes_field(self, mock_supabase):
        """
        Інтеграційний: update() змінює значення поля,
        результат містить нове значення.
        """
        # Мок повертає оновлений запис
        mock_supabase.table.return_value.update.return_value \
            .eq.return_value.eq.return_value \
            .execute.return_value.data = [
                {'id': 'test-id', 'type': 'income',
                 'amount': '250', 'category_id': None}
            ]
        # Мок для _enrich (select категорії)
        mock_supabase.table.return_value.select.return_value \
            .eq.return_value.execute.return_value.data = []

        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import TransactionRepository
            repo = TransactionRepository()

            updated = await repo.update('test-id', 'user-1', {'amount': 250.0})

        # Assert: поле amount змінилось
        assert updated is not None
        assert updated['amount'] == '250'
        assert updated['id'] == 'test-id'

        # Assert: update() був викликаний з правильними аргументами
        mock_supabase.table.return_value.update.assert_called_once_with(
            {'amount': 250.0}
        )

    # ──────────────────────────────────────────────────────────
    # TEST 3: delete → видаляє запис, повертає True
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_delete_removes_record(self, mock_supabase):
        """
        Інтеграційний: delete() видаляє транзакцію,
        повертає True і запис більше недоступний.
        """
        # Мок для delete
        mock_supabase.table.return_value.delete.return_value \
            .eq.return_value.eq.return_value \
            .execute.return_value.data = [{'id': 'test-id'}]

        # Мок для get_by_id після видалення — повертає None
        mock_supabase.table.return_value.select.return_value \
            .eq.return_value.eq.return_value \
            .single.return_value.execute.return_value.data = None

        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import TransactionRepository
            repo = TransactionRepository()

            # Act: видалити
            result = await repo.delete('test-id', 'user-1')

            # Assert: повернув True
            assert result is True

            # Assert: після видалення get_by_id повертає None
            after = await repo.get_by_id('test-id', 'user-1')
            assert after is None

    # ──────────────────────────────────────────────────────────
    # TEST 4: get_all — повертає список транзакцій юзера
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_get_all_returns_user_transactions(self, mock_supabase):
        """
        Інтеграційний: get_all() повертає лише транзакції
        конкретного користувача.
        """
        fake_list = [
            {'id': 'tx-1', 'type': 'income',  'amount': '100',
             'user_id': 'user-1', 'category': None,
             'transaction_date': '2024-04-02'},
            {'id': 'tx-2', 'type': 'expense', 'amount': '50',
             'user_id': 'user-1', 'category': None,
             'transaction_date': '2024-04-01'},
        ]
        mock_supabase.table.return_value.select.return_value \
            .eq.return_value.order.return_value \
            .range.return_value.execute.return_value.data = fake_list

        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import TransactionRepository
            repo = TransactionRepository()

            result = await repo.get_all('user-1')

        assert len(result) == 2
        assert all(t['user_id'] == 'user-1' for t in result)
        # перший — income, другий — expense
        assert result[0]['type'] == 'income'
        assert result[1]['type'] == 'expense'


# ══════════════════════════════════════════════════════════════
# INTEGRATION TESTS — CategoryRepository
# ══════════════════════════════════════════════════════════════

class TestCategoryRepositoryIntegration:

    # ──────────────────────────────────────────────────────────
    # TEST 5: create → повертає нову категорію
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_create_category(self, mock_supabase):
        mock_supabase.table.return_value.insert.return_value \
            .execute.return_value.data = [
                {'id': 'cat-1', 'name': 'Food',
                 'icon': '🍔', 'color': '#F97316',
                 'type': 'expense', 'user_id': 'user-1'}
            ]

        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import CategoryRepository
            repo = CategoryRepository()

            result = await repo.create('user-1', {
                'name': 'Food', 'icon': '🍔',
                'color': '#F97316', 'type': 'expense'
            })

        assert result['id'] == 'cat-1'
        assert result['name'] == 'Food'
        assert result['type'] == 'expense'

    # ──────────────────────────────────────────────────────────
    # TEST 6: delete категорії → повертає True
    # ──────────────────────────────────────────────────────────
    @pytest.mark.asyncio
    async def test_delete_category_returns_true(self, mock_supabase):
        mock_supabase.table.return_value.delete.return_value \
            .eq.return_value.eq.return_value \
            .execute.return_value.data = [{'id': 'cat-1'}]

        with patch('src.repositories.repositories.get_supabase_admin',
                   return_value=mock_supabase):

            from src.repositories.repositories import CategoryRepository
            repo = CategoryRepository()

            result = await repo.delete('cat-1', 'user-1')

        assert result is True