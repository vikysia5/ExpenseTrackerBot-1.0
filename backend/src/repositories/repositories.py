"""
Transaction Repository - Data Access Layer
All Supabase queries for transactions
"""
from typing import Optional, List
from decimal import Decimal
from src.core.database import get_supabase_admin
from src.core.logger import logger


class TransactionRepository:
    def __init__(self):
        self.db = get_supabase_admin()
        self.table = "transactions"

    async def create(self, user_id: str, data: dict) -> dict:
        tag_ids = data.pop("tag_ids", [])
        row = {**data, "user_id": user_id}
        if row.get("amount"):
            row["amount"] = float(row["amount"])
        if row.get("transaction_date"):
            if hasattr(row["transaction_date"], "isoformat"):
                row["transaction_date"] = row["transaction_date"].isoformat()

        result = self.db.table(self.table).insert(row).execute()
        tx = result.data[0] if result.data else {}

        # Link tags
        if tag_ids and tx.get("id"):
            tag_links = [{"transaction_id": tx["id"], "tag_id": tid} for tid in tag_ids]
            self.db.table("expense_tags").insert(tag_links).execute()

        logger.info("Transaction created", id=tx.get("id"), user=user_id)
        return await self._enrich(tx)

    async def get_by_id(self, tx_id: str, user_id: str) -> Optional[dict]:
        result = self.db.table(self.table).select(
            "*, category:categories(*)"
        ).eq("id", tx_id).eq("user_id", user_id).single().execute()
        return result.data

    async def get_all(
        self,
        user_id: str,
        type_filter: Optional[str] = None,
        category_id: Optional[str] = None,
        month: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        query = self.db.table(self.table).select(
            "*, category:categories(*)"
        ).eq("user_id", user_id).order("transaction_date", desc=True)

        if type_filter:
            query = query.eq("type", type_filter)
        if category_id:
            query = query.eq("category_id", category_id)
        if month:
            # month format: "2024-04"
            start = f"{month}-01"
            parts = month.split("-")
            year, m = int(parts[0]), int(parts[1])
            if m == 12:
                end = f"{year + 1}-01-01"
            else:
                end = f"{year}-{m + 1:02d}-01"
            query = query.gte("transaction_date", start).lt("transaction_date", end)

        result = query.range(offset, offset + limit - 1).execute()
        return result.data or []

    async def update(self, tx_id: str, user_id: str, data: dict) -> Optional[dict]:
        data.pop("tag_ids", None)
        if data.get("amount"):
            data["amount"] = float(data["amount"])
        if data.get("transaction_date") and hasattr(data["transaction_date"], "isoformat"):
            data["transaction_date"] = data["transaction_date"].isoformat()

        result = self.db.table(self.table).update(data).eq("id", tx_id).eq("user_id", user_id).execute()
        if result.data:
            return await self._enrich(result.data[0])
        return None

    async def delete(self, tx_id: str, user_id: str) -> bool:
        result = self.db.table(self.table).delete().eq("id", tx_id).eq("user_id", user_id).execute()
        logger.info("Transaction deleted", id=tx_id)
        return bool(result.data)

    async def get_stats(self, user_id: str, month: Optional[str] = None) -> dict:
        data = await self.get_all(user_id, month=month, limit=1000)
        income = sum(float(t["amount"]) for t in data if t["type"] == "income")
        expense = sum(float(t["amount"]) for t in data if t["type"] == "expense")

        # By category
        cat_totals: dict = {}
        for t in data:
            cat = (t.get("category") or {}).get("name", "Other")
            key = (cat, t["type"])
            cat_totals[key] = cat_totals.get(key, 0) + float(t["amount"])

        by_category = [{"name": k[0], "type": k[1], "total": v} for k, v in cat_totals.items()]

        return {
            "total_income": income,
            "total_expense": expense,
            "balance": income - expense,
            "by_category": by_category,
        }

    async def _enrich(self, tx: dict) -> dict:
        if not tx.get("category_id"):
            return tx
        cat = self.db.table("categories").select("*").eq("id", tx["category_id"]).execute()
        tx["category"] = cat.data[0] if cat.data else None
        return tx


class CategoryRepository:
    def __init__(self):
        self.db = get_supabase_admin()
        self.table = "categories"

    async def get_all(self, user_id: str) -> list:
        result = self.db.table(self.table).select("*").or_(
            f"user_id.eq.{user_id},is_default.eq.true"
        ).execute()
        return result.data or []

    async def create(self, user_id: str, data: dict) -> dict:
        row = {**data, "user_id": user_id}
        result = self.db.table(self.table).insert(row).execute()
        return result.data[0]

    async def update(self, cat_id: str, user_id: str, data: dict) -> Optional[dict]:
        result = self.db.table(self.table).update(data).eq("id", cat_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    async def delete(self, cat_id: str, user_id: str) -> bool:
        result = self.db.table(self.table).delete().eq("id", cat_id).eq("user_id", user_id).execute()
        return bool(result.data)


class UserRepository:
    def __init__(self):
        self.db = get_supabase_admin()
        self.table = "users"

    async def create(self, data: dict) -> dict:
        result = self.db.table(self.table).insert(data).select("*").execute()
        if result.error:
            logger.error("Failed to create user", error=result.error)
            raise Exception(result.error)
        user = result.data[0] if result.data else None
        logger.info("User create result", user_id=user.get("id") if user else None, data=list(data.keys()))
        return user

    async def get_by_email(self, email: str) -> Optional[dict]:
        result = self.db.table(self.table).select("*").eq("email", email).execute()
        return result.data[0] if result.data else None

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        result = self.db.table(self.table).select("*").eq("telegram_id", telegram_id).execute()
        return result.data[0] if result.data else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        result = self.db.table(self.table).select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None

    async def upsert_telegram_user(self, telegram_data: dict) -> dict:
        existing = await self.get_by_telegram_id(telegram_data["id"])
        if existing:
            return existing
        
        # Build user dict with telegram_id and optional fields
        user = {
            "telegram_id": telegram_data["id"],
        }
        
        # Try to add optional fields
        optional_fields = ["first_name", "last_name", "username"]
        for field in optional_fields:
            if field in telegram_data:
                user[field] = telegram_data.get(field)
        
        try:
            return await self.create(user)
        except Exception as e:
            # If error is about missing columns, create with only telegram_id
            if "PGRST204" in str(e) or "column" in str(e).lower():
                logger.warning("Columns don't exist in schema, creating with minimal data", error=str(e))
                user = {"telegram_id": telegram_data["id"]}
                return await self.create(user)
            raise
