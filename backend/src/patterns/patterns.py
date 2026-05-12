"""
Design Patterns Implementation
- Factory Method: PaymentFactory / NotifierFactory
- Builder: ExpenseBuilder
- Strategy: SortStrategy
- Observer: EventBus (UI updates)
- Facade: TransactionFacade
"""
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from decimal import Decimal
from typing import Optional, List, Callable, Dict
from uuid import uuid4
from src.core.logger import logger


# ============================================
# FACTORY METHOD - Payment Methods
# ============================================
class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: Decimal) -> dict:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class CashPayment(PaymentProcessor):
    def process(self, amount: Decimal) -> dict:
        logger.info("Processing cash payment", amount=str(amount))
        return {"method": "cash", "amount": float(amount), "fee": 0.0}

    def get_name(self) -> str:
        return "cash"


class CardPayment(PaymentProcessor):
    def process(self, amount: Decimal) -> dict:
        fee = float(amount) * 0.015  # 1.5% fee
        logger.info("Processing card payment", amount=str(amount), fee=fee)
        return {"method": "card", "amount": float(amount), "fee": fee}

    def get_name(self) -> str:
        return "card"


class CryptoPayment(PaymentProcessor):
    def process(self, amount: Decimal) -> dict:
        fee = float(amount) * 0.01  # 1% fee
        logger.info("Processing crypto payment", amount=str(amount), fee=fee)
        return {"method": "crypto", "amount": float(amount), "fee": fee}

    def get_name(self) -> str:
        return "crypto"


class PaymentFactory:
    """Factory Method: creates payment processor by type"""
    _processors: Dict[str, type] = {
        "cash": CashPayment,
        "card": CardPayment,
        "crypto": CryptoPayment,
    }

    @classmethod
    def create(cls, payment_method: str) -> PaymentProcessor:
        processor_class = cls._processors.get(payment_method)
        if not processor_class:
            logger.warning("Unknown payment method, using card", method=payment_method)
            processor_class = CardPayment
        return processor_class()

    @classmethod
    def register(cls, name: str, processor: type):
        cls._processors[name] = processor


# ============================================
# FACTORY METHOD - Notifiers
# ============================================
class Notifier(ABC):
    @abstractmethod
    async def send(self, user_id: str, message: str) -> bool:
        pass


class TelegramNotifier(Notifier):
    async def send(self, user_id: str, message: str) -> bool:
        logger.info("Sending Telegram notification", user_id=user_id, msg=message[:50])
        # In production: call Telegram Bot API
        return True


class EmailNotifier(Notifier):
    async def send(self, user_id: str, message: str) -> bool:
        logger.info("Sending Email notification", user_id=user_id, msg=message[:50])
        # In production: call email service
        return True


class NotifierFactory:
    @staticmethod
    def create(channel: str) -> Notifier:
        if channel == "telegram":
            return TelegramNotifier()
        elif channel == "email":
            return EmailNotifier()
        else:
            return TelegramNotifier()


# ============================================
# BUILDER - ExpenseBuilder
# ============================================
class ExpenseData:
    def __init__(self):
        self.id = str(uuid4())
        self.type = "expense"
        self.amount = Decimal("0")
        self.currency = "USD"
        self.category_id = None
        self.comment = None
        self.payment_method = "card"
        self.transaction_date = datetime.now(UTC)
        self.tag_ids = []


class ExpenseBuilder:
    """Builder Pattern: step-by-step transaction creation"""

    def __init__(self):
        self._expense = ExpenseData()

    def set_type(self, tx_type: str) -> "ExpenseBuilder":
        assert tx_type in ("income", "expense")
        self._expense.type = tx_type
        return self

    def set_amount(self, amount: Decimal, currency: str = "USD") -> "ExpenseBuilder":
        assert amount > 0, "Amount must be positive"
        self._expense.amount = amount
        self._expense.currency = currency
        return self

    def set_category(self, category_id: Optional[str]) -> "ExpenseBuilder":
        self._expense.category_id = category_id
        return self

    def set_comment(self, comment: Optional[str]) -> "ExpenseBuilder":
        self._expense.comment = comment
        return self

    def set_payment_method(self, method: str) -> "ExpenseBuilder":
        self._expense.payment_method = method
        return self

    def set_date(self, date: Optional[datetime]) -> "ExpenseBuilder":
        if date:
            self._expense.transaction_date = date
        return self

    def add_tags(self, tag_ids: List[str]) -> "ExpenseBuilder":
        self._expense.tag_ids = tag_ids
        return self

    def build(self) -> ExpenseData:
        logger.debug("ExpenseBuilder.build()", type=self._expense.type, amount=str(self._expense.amount))
        return self._expense

    def to_dict(self) -> dict:
        data = self.build()
        return {
            "type": data.type,
            "amount": float(data.amount),
            "currency": data.currency,
            "category_id": data.category_id,
            "comment": data.comment,
            "payment_method": data.payment_method,
            "transaction_date": data.transaction_date.isoformat(),
        }


# ============================================
# STRATEGY - Sorting
# ============================================
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, transactions: List[dict]) -> List[dict]:
        pass


class SortByDate(SortStrategy):
    def sort(self, transactions: List[dict]) -> List[dict]:
        return sorted(transactions, key=lambda x: x.get("transaction_date", ""), reverse=True)


class SortByAmount(SortStrategy):
    def sort(self, transactions: List[dict]) -> List[dict]:
        return sorted(transactions, key=lambda x: float(x.get("amount", 0)), reverse=True)


class SortByCategory(SortStrategy):
    def sort(self, transactions: List[dict]) -> List[dict]:
        return sorted(transactions, key=lambda x: (x.get("category") or {}).get("name", ""))


class TransactionSorter:
    """Context for Strategy pattern"""
    _strategies = {
        "date": SortByDate,
        "amount": SortByAmount,
        "category": SortByCategory,
    }

    def __init__(self, strategy_name: str = "date"):
        strategy_class = self._strategies.get(strategy_name, SortByDate)
        self._strategy = strategy_class()

    def sort(self, transactions: List[dict]) -> List[dict]:
        return self._strategy.sort(transactions)


# ============================================
# OBSERVER - EventBus
# ============================================
class EventBus:
    """Observer Pattern: publish/subscribe for transaction events"""
    _instance = None
    _listeners: Dict[str, List[Callable]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = {}
        return cls._instance

    def subscribe(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        logger.debug("EventBus.subscribe", event=event)

    def unsubscribe(self, event: str, callback: Callable):
        if event in self._listeners:
            self._listeners[event].remove(callback)

    async def publish(self, event: str, data: dict):
        logger.info("EventBus.publish", event=event)
        for callback in self._listeners.get(event, []):
            try:
                await callback(data)
            except Exception as e:
                logger.error("EventBus callback error", event=event, error=str(e))


event_bus = EventBus()
