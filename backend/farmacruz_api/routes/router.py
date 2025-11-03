from fastapi import APIRouter
from . import auth, products, orders, admin, categories

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categorías"])
api_router.include_router(products.router, prefix="/products", tags=["Productos"])
api_router.include_router(orders.router, prefix="/orders", tags=["Pedidos"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administración"])