# tests/unit/test_validators.py
import pytest
from decimal import Decimal
from pydantic import ValidationError
from src.models.schemas import TransactionCreate, CategoryCreate

class TestTransactionCreate:
    def test_valid_income_transaction_passes(self):
        data = {'type':'income','amount':Decimal('100.00')}
        result = TransactionCreate(**data)
        assert result.type == 'income'

    def test_valid_expense_transaction_passes(self):
        data = {'type':'expense','amount':Decimal('50.50')}
        result = TransactionCreate(**data)
        assert result.amount == Decimal('50.50')

    def test_default_currency_is_usd(self):
        data = {'type':'income','amount':Decimal('10')}
        result = TransactionCreate(**data)
        assert result.currency == 'USD'

    def test_default_payment_method_is_card(self):
        data = {'type':'expense','amount':Decimal('20')}
        result = TransactionCreate(**data)
        assert result.payment_method == 'card'

    def test_optional_comment_accepts_none(self):
        data = {'type':'income','amount':Decimal('5')}
        result = TransactionCreate(**data)
        assert result.comment is None

    def test_negative_amount_raises_error(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type='expense', amount=Decimal('-10'))

    def test_zero_amount_raises_error(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type='income', amount=Decimal('0'))

    def test_invalid_type_raises_error(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type='transfer', amount=Decimal('10'))

    def test_invalid_payment_method_raises_error(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type='income', amount=Decimal('10'),
                payment_method='paypal')

    def test_missing_amount_raises_error(self):
        with pytest.raises(ValidationError):
            TransactionCreate(type='income')
