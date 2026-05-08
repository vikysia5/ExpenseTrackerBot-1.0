# RED: tests/unit/test_balance.py


def test_balance_income_minus_expense():
    txs = [{'type':'income','amount':500},
           {'type':'expense','amount':200}]
    assert calculate_balance(txs) == 300.0

def test_balance_empty_list_returns_zero():
    assert calculate_balance([]) == 0.0

def test_balance_only_expenses_is_negative():
    txs = [{'type':'expense','amount':100}]
    assert calculate_balance(txs) == -100.0

# GREEN + REFACTOR: src/core/utils.py
from typing import List

def calculate_balance(transactions: List[dict]) -> float:
    if not transactions:
        return 0.0
    income = sum(float(t['amount']) for t in transactions
                 if t.get('type') == 'income')
    expense = sum(float(t['amount']) for t in transactions
                  if t.get('type') == 'expense')
    return round(income - expense, 2)
