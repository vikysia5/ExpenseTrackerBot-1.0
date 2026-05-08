# src/validators/expense_validator.py
# ПР-10, Крок 5: Валідатор вхідних даних для витрат

from datetime import date
from src.exceptions import ValidationError

ALLOWED_CATEGORIES = {
    "food", "transport", "housing", "health", "entertainment",
    "shopping", "education", "travel", "salary", "freelance",
    "investment", "gift", "other"
}

ALLOWED_TYPES = {"expense", "income"}

MAX_DESCRIPTION_LENGTH = 200
MIN_AMOUNT = 0.01
MAX_AMOUNT = 999_999_999.99


class ExpenseValidator:
    """
    Валідує дані витрати на межі системи —
    до того як вони потраплять у бізнес-логіку.
    Кидає ValidationError при першій знайденій помилці.
    """

    @classmethod
    def validate(cls, data: dict) -> dict:
        """
        Перевіряє і повертає очищені дані.
        Кидає ValidationError якщо щось не так.
        """
        cls._validate_amount(data.get("amount"))
        cls._validate_type(data.get("type", "expense"))
        cls._validate_category(data.get("category", "other"))
        cls._validate_description(data.get("description", ""))
        cls._validate_date(data.get("date"))

        # Повертаємо очищені (sanitized) дані
        return {
            "amount":      round(float(data["amount"]), 2),
            "type":        data.get("type", "expense"),
            "category":    data.get("category", "other"),
            "description": str(data.get("description", "")).strip()[:MAX_DESCRIPTION_LENGTH],
            "currency":    data.get("currency", "USD"),
            "date":        data.get("date") or date.today().isoformat(),
        }

    # ── Приватні методи валідації ─────────────────────────────────

    @staticmethod
    def _validate_amount(amount) -> None:
        """Перевірка обов'язкового поля amount."""
        if amount is None:
            raise ValidationError("amount", "Обов'язкове поле")
        try:
            value = float(amount)
        except (TypeError, ValueError):
            raise ValidationError("amount", "Має бути числом")
        if value < MIN_AMOUNT:
            raise ValidationError("amount", f"Має бути більше {MIN_AMOUNT}")
        if value > MAX_AMOUNT:
            raise ValidationError("amount", f"Занадто велике значення")

    @staticmethod
    def _validate_type(type_val: str) -> None:
        """Перевірка допустимих значень (enum)."""
        if type_val not in ALLOWED_TYPES:
            raise ValidationError(
                "type",
                f"Допустимі значення: {', '.join(sorted(ALLOWED_TYPES))}"
            )

    @staticmethod
    def _validate_category(category: str) -> None:
        """Перевірка допустимих значень категорії (enum)."""
        if category not in ALLOWED_CATEGORIES:
            raise ValidationError(
                "category",
                f"Недопустима категорія. Доступні: {', '.join(sorted(ALLOWED_CATEGORIES))}"
            )

    @staticmethod
    def _validate_description(description: str) -> None:
        """Перевірка довжини рядка."""
        if len(str(description)) > MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                "description",
                f"Максимальна довжина — {MAX_DESCRIPTION_LENGTH} символів"
            )

    @staticmethod
    def _validate_date(date_val) -> None:
        """Перевірка формату дати (якщо передана)."""
        if not date_val:
            return  # поле необов'язкове
        try:
            date.fromisoformat(str(date_val))
        except ValueError:
            raise ValidationError(
                "date",
                "Невірний формат дати. Очікується: YYYY-MM-DD"
            )
