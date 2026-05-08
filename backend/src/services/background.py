"""
Фонові задачі — Background Tasks
=================================
Операція: відправка Telegram-сповіщення після створення транзакції.

Чому саме ця операція?
- Зовнішній API (Telegram) може відповідати повільно
- Користувач не повинен чекати — транзакція вже збережена
- Якщо сповіщення не дійде — це не критично для бізнес-логіки

Реалізація:
- Синхронна функція send_notification()
- Запуск через FastAPI BackgroundTasks
- Логування початку, кінця задачі через Logger (Singleton)
"""

import time
import httpx
from typing import Optional
from src.core.logger import logger
from src.core.config import settings


# ============================================
# ФОНОВА ФУНКЦІЯ (синхронна)
# ============================================
def send_notification(
    user_telegram_id: int,
    message: str,
    tx_type: str,
    amount: float,
    category: Optional[str] = None,
) -> None:
    """
    Відправляє Telegram-повідщення користувачу.
    Виконується у фоні — не блокує HTTP-відповідь.

    Args:
        user_telegram_id: Telegram ID юзера
        message:          Текст повідомлення
        tx_type:          'income' або 'expense'
        amount:           Сума транзакції
        category:         Назва категорії (опційно)
    """
    # ── Логування ПОЧАТКУ фонової задачі ──
    logger.info(
        "[BG TASK] Початок відправки сповіщення",
        telegram_id=user_telegram_id,
        type=tx_type,
        amount=amount,
    )
    start = time.perf_counter()

    try:
        sign = "➕" if tx_type == "income" else "➖"
        cat_line = f"📂 {category}" if category else ""
        text = (
            f"{sign} *{'Income' if tx_type == 'income' else 'Expense'}*\n"
            f"💰 Amount: `${amount:.2f}`\n"
            f"{cat_line}\n"
            f"📝 {message}"
        ).strip()

        if settings.TELEGRAM_BOT_TOKEN:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            response = httpx.post(
                url,
                json={
                    "chat_id": user_telegram_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=5.0,
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - start

            # ── Логування КІНЦЯ фонової задачі ──
            logger.info(
                "[BG TASK] Сповіщення відправлено успішно",
                telegram_id=user_telegram_id,
                status=response.status_code,
                elapsed=f"{elapsed:.3f}с",
            )
        else:
            # Режим розробки — токен не задано
            elapsed = time.perf_counter() - start
            logger.info(
                "[BG TASK] Dev-режим: сповіщення пропущено (немає TELEGRAM_BOT_TOKEN)",
                elapsed=f"{elapsed:.3f}с",
            )

    except httpx.TimeoutException:
        elapsed = time.perf_counter() - start
        logger.error(
            "[BG TASK] Таймаут при відправці сповіщення",
            telegram_id=user_telegram_id,
            elapsed=f"{elapsed:.3f}с",
        )
    except httpx.HTTPStatusError as e:
        logger.error(
            "[BG TASK] HTTP помилка Telegram API",
            status=e.response.status_code,
            detail=e.response.text[:100],
        )
    except Exception as e:
        logger.error(
            "[BG TASK] Невідома помилка при відправці",
            error=str(e),
        )
