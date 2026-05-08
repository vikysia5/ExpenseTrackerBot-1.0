# tests/test_exceptions.py
# ПР-10, Крок 6: Тести для власних виключень

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.exceptions import (
    AppError,
    ValidationError,
    ExpenseNotFoundError,
    UserNotFoundError,
    CategoryNotFoundError,
    BudgetExceededError,
    DatabaseError,
    BusinessError,
)


# ── Тести ValidationError ─────────────────────────────────────────

def test_validation_error_has_field():
    """ValidationError зберігає назву поля."""
    err = ValidationError("amount", "занадто маленьке")
    assert err.field == "amount"
    assert "amount" in str(err)
    assert "занадто маленьке" in str(err)
    print("✅ test_validation_error_has_field")


def test_validation_error_to_dict():
    """to_dict() повертає field разом з error і message."""
    err = ValidationError("category", "невірна категорія")
    d = err.to_dict()
    assert d["error"] == "VALIDATION_ERROR"
    assert d["field"] == "category"
    assert "category" in d["message"]
    print("✅ test_validation_error_to_dict")


# ── Тести ExpenseNotFoundError ────────────────────────────────────

def test_expense_not_found_dict():
    """ExpenseNotFoundError повертає правильний code і message."""
    err = ExpenseNotFoundError(99)
    d = err.to_dict()
    assert d["error"] == "EXPENSE_NOT_FOUND"
    assert "99" in d["message"]
    print("✅ test_expense_not_found_dict")


def test_expense_not_found_stores_id():
    """ExpenseNotFoundError зберігає expense_id."""
    err = ExpenseNotFoundError(42)
    assert err.expense_id == 42
    print("✅ test_expense_not_found_stores_id")


# ── Тести UserNotFoundError ───────────────────────────────────────

def test_user_not_found_dict():
    """UserNotFoundError повертає правильний code."""
    err = UserNotFoundError(7)
    d = err.to_dict()
    assert d["error"] == "USER_NOT_FOUND"
    assert "7" in d["message"]
    print("✅ test_user_not_found_dict")


# ── Тести ієрархії ────────────────────────────────────────────────

def test_business_error_hierarchy():
    """Всі бізнес-помилки є підкласами AppError."""
    assert isinstance(ExpenseNotFoundError(1), AppError)
    assert isinstance(UserNotFoundError(1), AppError)
    assert isinstance(CategoryNotFoundError("food"), AppError)
    assert isinstance(BudgetExceededError(100, 150), AppError)
    print("✅ test_business_error_hierarchy")


def test_database_error_hierarchy():
    """DatabaseError також є підкласом AppError."""
    err = DatabaseError("insert", "connection refused")
    assert isinstance(err, AppError)
    assert "insert" in err.message
    assert err.code == "DB_ERROR"
    print("✅ test_database_error_hierarchy")


def test_budget_exceeded_stores_values():
    """BudgetExceededError зберігає limit і actual."""
    err = BudgetExceededError(limit=500.0, actual=750.0, currency="USD")
    assert err.limit == 500.0
    assert err.actual == 750.0
    assert "500" in err.message
    assert "750" in err.message
    print("✅ test_budget_exceeded_stores_values")


def test_app_error_base_to_dict():
    """Базовий AppError.to_dict() повертає error і message."""
    err = AppError("щось пішло не так", "CUSTOM_CODE")
    d = err.to_dict()
    assert d["error"] == "CUSTOM_CODE"
    assert d["message"] == "щось пішло не так"
    print("✅ test_app_error_base_to_dict")


# ── Тести валідатора ──────────────────────────────────────────────

def test_validator_raises_on_missing_amount():
    """ValidationError кидається якщо amount відсутній."""
    from src.validators.expense_validator import ExpenseValidator
    try:
        ExpenseValidator.validate({"category": "food"})
        assert False, "Мав кинути ValidationError"
    except ValidationError as e:
        assert e.field == "amount"
    print("✅ test_validator_raises_on_missing_amount")


def test_validator_raises_on_bad_category():
    """ValidationError кидається для невідомої категорії."""
    from src.validators.expense_validator import ExpenseValidator
    try:
        ExpenseValidator.validate({"amount": 100, "category": "НЕВІДОМА"})
        assert False, "Мав кинути ValidationError"
    except ValidationError as e:
        assert e.field == "category"
    print("✅ test_validator_raises_on_bad_category")


def test_validator_raises_on_bad_date():
    """ValidationError кидається для неправильного формату дати."""
    from src.validators.expense_validator import ExpenseValidator
    try:
        ExpenseValidator.validate({"amount": 50, "date": "31-12-2024"})
        assert False, "Мав кинути ValidationError"
    except ValidationError as e:
        assert e.field == "date"
    print("✅ test_validator_raises_on_bad_date")


def test_validator_returns_clean_data():
    """validate() повертає очищені дані при успіху."""
    from src.validators.expense_validator import ExpenseValidator
    result = ExpenseValidator.validate({
        "amount": "99.9",
        "type": "expense",
        "category": "food",
        "description": "  обід  ",
        "date": "2024-12-31"
    })
    assert result["amount"] == 99.9
    assert result["description"] == "обід"  # trim
    assert result["date"] == "2024-12-31"
    print("✅ test_validator_returns_clean_data")


# ── Запуск усіх тестів ────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*50)
    print("ПР-10: Запуск тестів виключень")
    print("="*50 + "\n")

    test_validation_error_has_field()
    test_validation_error_to_dict()
    test_expense_not_found_dict()
    test_expense_not_found_stores_id()
    test_user_not_found_dict()
    test_business_error_hierarchy()
    test_database_error_hierarchy()
    test_budget_exceeded_stores_values()
    test_app_error_base_to_dict()
    test_validator_raises_on_missing_amount()
    test_validator_raises_on_bad_category()
    test_validator_raises_on_bad_date()
    test_validator_returns_clean_data()

    print("\n" + "="*50)
    print("✅ Всі тести пройдено!")
    print("="*50)
