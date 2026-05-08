# src/exceptions.py
# ── Базовий клас ──────────────────────────────────────────────────
class AppError(Exception):
    """
    Базовий клас для всіх помилок застосунку.
    Дозволяє відловити БУДЬ-яку помилку: except AppError as e
    """
    def __init__(self, message: str, code: str = "APP_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code

    def to_dict(self) -> dict:
        """Для повернення в API як JSON."""
        return {
            "error": self.code,
            "message": self.message
        }

    def __str__(self):
        return f"[{self.code}] {self.message}"


# ── Помилки валідації ─────────────────────────────────────────────
class ValidationError(AppError):
    """Вхідні дані не пройшли валідацію."""
    def __init__(self, field: str, message: str):
        super().__init__(
            message=f"Поле '{field}': {message}",
            code="VALIDATION_ERROR"
        )
        self.field = field

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "field": self.field
        }


# ── Бізнес-помилки ────────────────────────────────────────────────
class BusinessError(AppError):
    """Базовий клас для порушень бізнес-логіки."""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(message=message, code=code)


class ExpenseNotFoundError(BusinessError):
    """Витрату з вказаним ID не знайдено."""
    def __init__(self, expense_id: int):
        super().__init__(
            message=f"Витрату #{expense_id} не знайдено",
            code="EXPENSE_NOT_FOUND"
        )
        self.expense_id = expense_id


class UserNotFoundError(BusinessError):
    """Користувача з вказаним ID не знайдено."""
    def __init__(self, user_id: int):
        super().__init__(
            message=f"Користувача #{user_id} не знайдено",
            code="USER_NOT_FOUND"
        )
        self.user_id = user_id


class CategoryNotFoundError(BusinessError):
    """Категорію не знайдено."""
    def __init__(self, category: str):
        super().__init__(
            message=f"Категорію '{category}' не знайдено",
            code="CATEGORY_NOT_FOUND"
        )
        self.category = category


class BudgetExceededError(BusinessError):
    """Перевищено ліміт бюджету."""
    def __init__(self, limit: float, actual: float, currency: str = "USD"):
        super().__init__(
            message=f"Перевищено бюджет: ліміт {limit} {currency}, фактично {actual} {currency}",
            code="BUDGET_EXCEEDED"
        )
        self.limit = limit
        self.actual = actual


# ── Інфраструктурні помилки ───────────────────────────────────────
class InfrastructureError(AppError):
    """Зовнішні залежності недоступні."""
    def __init__(self, message: str, code: str = "INFRASTRUCTURE_ERROR"):
        super().__init__(message=message, code=code)


class DatabaseError(InfrastructureError):
    """Помилка при роботі з базою даних."""
    def __init__(self, operation: str, detail: str):
        super().__init__(
            message=f"БД: операція '{operation}' не вдалась: {detail}",
            code="DB_ERROR"
        )
        self.operation = operation
