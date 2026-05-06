"""
Services - Business Logic Layer
Includes Facade pattern for transaction operations
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from src.core.logger import logger
from src.core.security import hash_password, verify_password, create_access_token
from src.models.schemas import TransactionCreate, TransactionUpdate
from src.patterns.patterns import (
    ExpenseBuilder, PaymentFactory, NotifierFactory,
    TransactionSorter, event_bus
)
from src.repositories.repositories import (
    TransactionRepository, CategoryRepository, UserRepository
)


# ============================================
# AUTH SERVICE
# ============================================
class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def register(self, email: str, password: str, username: Optional[str] = None) -> dict:
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        user_data = {
            "email": email,
            "password_hash": hash_password(password),
            "username": username,
        }
        user = await self.user_repo.create(user_data)
        token = create_access_token({"sub": user["id"], "email": email})
        logger.info("User registered", user_id=user["id"])
        return {"access_token": token, "token_type": "bearer", "user": user}

    async def login(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid credentials")
        token = create_access_token({"sub": user["id"], "email": email})
        logger.info("User logged in", user_id=user["id"])
        return {"access_token": token, "token_type": "bearer", "user": user}

    async def telegram_login(self, telegram_data: dict) -> dict:
        user = await self.user_repo.upsert_telegram_user(telegram_data)
        token = create_access_token({"sub": user["id"], "telegram_id": telegram_data["id"]})
        logger.info("Telegram login", user_id=user["id"], tg=telegram_data["id"])
        return {"access_token": token, "token_type": "bearer", "user": user}


# ============================================
# TRANSACTION FACADE
# Facade: single service for create + notify + log
# ============================================
class TransactionFacade:
    """
    Facade Pattern: unified interface for transaction lifecycle:
    1. Build transaction (Builder)
    2. Process payment (Factory)
    3. Save to DB (Repository)
    4. Notify user (Factory)
    5. Publish event (Observer)
    6. Log (Singleton)
    """

    def __init__(self):
        self.tx_repo = TransactionRepository()

    async def create_transaction(self, user_id: str, data: TransactionCreate) -> dict:
        # 1. Build expense using Builder pattern
        builder = (
            ExpenseBuilder()
            .set_type(data.type)
            .set_amount(data.amount, data.currency)
            .set_category(str(data.category_id) if data.category_id else None)
            .set_comment(data.comment)
            .set_payment_method(data.payment_method)
            .set_date(data.transaction_date)
            .add_tags([str(tid) for tid in (data.tag_ids or [])])
        )
        expense_data = builder.to_dict()
        expense_data["tag_ids"] = [str(tid) for tid in (data.tag_ids or [])]

        # 2. Process payment (Factory)
        processor = PaymentFactory.create(data.payment_method)
        payment_result = processor.process(data.amount)
        logger.info("Payment processed", result=payment_result)

        # 3. Save to DB (Repository)
        transaction = await self.tx_repo.create(user_id, expense_data)

        # 4. Notify user (Factory) - async fire-and-forget
        try:
            notifier = NotifierFactory.create("telegram")
            sign = "+" if data.type == "income" else "-"
            await notifier.send(
                user_id,
                f"Transaction recorded: {sign}{data.amount} {data.currency}"
            )
        except Exception as e:
            logger.warning("Notification failed", error=str(e))

        # 5. Publish Observer event
        await event_bus.publish("transaction.created", {
            "user_id": user_id,
            "transaction": transaction
        })

        return transaction

    async def get_transactions(
        self,
        user_id: str,
        type_filter: Optional[str] = None,
        category_id: Optional[str] = None,
        month: Optional[str] = None,
        sort_by: str = "date",
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        items = await self.tx_repo.get_all(
            user_id, type_filter, category_id, month, limit, offset
        )

        # Apply Strategy pattern sorting
        sorter = TransactionSorter(sort_by)
        items = sorter.sort(items)

        income_total = sum(float(t["amount"]) for t in items if t["type"] == "income")
        expense_total = sum(float(t["amount"]) for t in items if t["type"] == "expense")

        return {
            "items": items,
            "total": len(items),
            "income_total": income_total,
            "expense_total": expense_total,
            "balance": income_total - expense_total,
        }

    async def update_transaction(self, tx_id: str, user_id: str, data: TransactionUpdate) -> Optional[dict]:
        update_data = data.model_dump(exclude_unset=True)
        tx = await self.tx_repo.update(tx_id, user_id, update_data)

        if tx:
            await event_bus.publish("transaction.updated", {"user_id": user_id, "transaction": tx})

        return tx

    async def delete_transaction(self, tx_id: str, user_id: str) -> bool:
        deleted = await self.tx_repo.delete(tx_id, user_id)
        if deleted:
            await event_bus.publish("transaction.deleted", {"user_id": user_id, "tx_id": tx_id})
        return deleted

    async def get_stats(self, user_id: str, month: Optional[str] = None) -> dict:
        return await self.tx_repo.get_stats(user_id, month)


# ============================================
# CATEGORY SERVICE
# ============================================
class CategoryService:
    def __init__(self):
        self.cat_repo = CategoryRepository()

    async def get_all(self, user_id: str) -> list:
        return await self.cat_repo.get_all(user_id)

    async def create(self, user_id: str, data: dict) -> dict:
        return await self.cat_repo.create(user_id, data)

    async def update(self, cat_id: str, user_id: str, data: dict) -> Optional[dict]:
        return await self.cat_repo.update(cat_id, user_id, data)

    async def delete(self, cat_id: str, user_id: str) -> bool:
        return await self.cat_repo.delete(cat_id, user_id)
