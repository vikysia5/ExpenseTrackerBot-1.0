"""
API Routers - REST endpoints
OpenAPI 3.0 compliant
"""
from typing import Optional
from src.core.config import settings  # вот так
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.core.security import get_current_user, verify_telegram_init_data
from src.models.schemas import (
    UserCreate, UserLogin, TelegramAuth,
    TransactionCreate, TransactionUpdate,
    CategoryCreate, CategoryUpdate,
)
from src.services.services import AuthService, TransactionFacade, CategoryService

# ============================================
# AUTH ROUTER
# ============================================
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    try:
        return await auth_service.register(body.email, body.password, body.username)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@auth_router.post("/login")
async def login(body: UserLogin):
    try:
        return await auth_service.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


'''@auth_router.post("/telegram")
async def telegram_auth(body: TelegramAuth):
    telegram_data = verify_telegram_init_data(body.init_data)
    return await auth_service.telegram_login(telegram_data)'''

@auth_router.post("/telegram")
async def telegram_auth(data: TelegramAuth):
    try:
        user_data = verify_telegram_init_data(
            data.init_data, 
            settings.TELEGRAM_BOT_TOKEN
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Telegram auth failed: {e}")
    
    user = await auth_service.telegram_login(user_data)
    return user


@auth_router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    from src.repositories.repositories import UserRepository
    repo = UserRepository()
    user = await repo.get_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ============================================
# TRANSACTIONS ROUTER
# ============================================
tx_router = APIRouter(prefix="/expenses", tags=["Transactions"])
tx_facade = TransactionFacade()


@tx_router.get("")
async def list_transactions(
    type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category_id: Optional[str] = Query(None),
    month: Optional[str] = Query(None, description="Format: YYYY-MM"),
    sort_by: str = Query("date", pattern="^(date|amount|category)$"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user),
):
    return await tx_facade.get_transactions(
        current_user["sub"], type, category_id, month, sort_by, limit, offset
    )


@tx_router.post("", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await tx_facade.create_transaction(current_user["sub"], body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@tx_router.get("/stats")
async def get_stats(
    month: Optional[str] = Query(None, description="Format: YYYY-MM"),
    current_user: dict = Depends(get_current_user),
):
    return await tx_facade.get_stats(current_user["sub"], month)


@tx_router.get("/{tx_id}")
async def get_transaction(
    tx_id: str,
    current_user: dict = Depends(get_current_user),
):
    from src.repositories.repositories import TransactionRepository
    repo = TransactionRepository()
    tx = await repo.get_by_id(tx_id, current_user["sub"])
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@tx_router.put("/{tx_id}")
async def update_transaction(
    tx_id: str,
    body: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
):
    tx = await tx_facade.update_transaction(tx_id, current_user["sub"], body)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@tx_router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    tx_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await tx_facade.delete_transaction(tx_id, current_user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")


# ============================================
# CATEGORIES ROUTER
# ============================================
cat_router = APIRouter(prefix="/categories", tags=["Categories"])
cat_service = CategoryService()


@cat_router.get("")
async def list_categories(current_user: dict = Depends(get_current_user)):
    return await cat_service.get_all(current_user["sub"])


@cat_router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    current_user: dict = Depends(get_current_user),
):
    return await cat_service.create(current_user["sub"], body.model_dump())


@cat_router.put("/{cat_id}")
async def update_category(
    cat_id: str,
    body: CategoryUpdate,
    current_user: dict = Depends(get_current_user),
):
    cat = await cat_service.update(cat_id, current_user["sub"], body.model_dump(exclude_unset=True))
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@cat_router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    cat_id: str,
    current_user: dict = Depends(get_current_user),
):
    deleted = await cat_service.delete(cat_id, current_user["sub"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
