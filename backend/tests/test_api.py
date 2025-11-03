"""
Suite completa de tests para Farmacruz API
Ejecutar con: pytest tests/test_api_complete.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from farmacruz_api.main import app
from farmacruz_api.db.base import Base
from farmacruz_api.dependencies import get_db
from farmacruz_api.core.security import get_password_hash
from farmacruz_api.db.base import User, UserRole, Category, Product

# Base de datos en memoria para tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Variables globales para tests
admin_token = None
seller_token = None
customer_token = None
category_id = None
product_id = None
order_id = None
cart_item_id = None

# =============================================================================
# FIXTURES - Datos de prueba
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Crea usuarios iniciales para tests"""
    db = TestingSessionLocal()
    
    # Admin
    admin = User(
        username="admin_test",
        email="admin@test.com",
        password_hash=get_password_hash("admin123"),
        full_name="Admin Test",
        role=UserRole.admin,
        is_active=True
    )
    
    # Seller
    seller = User(
        username="seller_test",
        email="seller@test.com",
        password_hash=get_password_hash("seller123"),
        full_name="Seller Test",
        role=UserRole.seller,
        is_active=True
    )
    
    # Customer
    customer = User(
        username="customer_test",
        email="customer@test.com",
        password_hash=get_password_hash("customer123"),
        full_name="Customer Test",
        role=UserRole.customer,
        is_active=True
    )
    
    db.add_all([admin, seller, customer])
    db.commit()
    db.close()
    
    yield
    
    # Cleanup después de todos los tests
    Base.metadata.drop_all(bind=engine)

# =============================================================================
# TESTS DE AUTENTICACIÓN
# =============================================================================

class TestAuth:
    """Tests de autenticación y registro"""
    
    def test_root_endpoint(self):
        """Test del endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_register_new_user(self):
        """Test de registro de nuevo usuario"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "password123",
                "full_name": "New User",
                "role": "customer"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert "password" not in data
    
    def test_register_duplicate_username(self):
        """Test de registro con username duplicado"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "admin_test",
                "email": "another@test.com",
                "password": "password123",
                "full_name": "Another User",
                "role": "customer"
            }
        )
        assert response.status_code == 400
    
    def test_login_admin(self):
        """Test de login como admin"""
        global admin_token
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        admin_token = data["access_token"]
    
    def test_login_seller(self):
        """Test de login como seller"""
        global seller_token
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "seller_test",
                "password": "seller123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        seller_token = data["access_token"]
    
    def test_login_customer(self):
        """Test de login como customer"""
        global customer_token
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "customer_test",
                "password": "customer123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        customer_token = data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test de login con credenciales inválidas"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin_test",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test de obtener usuario actual"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin_test"
        assert data["role"] == "admin"

# =============================================================================
# TESTS DE CATEGORÍAS
# =============================================================================

class TestCategories:
    """Tests de gestión de categorías"""
    
    def test_create_category_as_seller(self):
        """Test de crear categoría como seller"""
        global category_id
        response = client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "name": "Medicamentos",
                "description": "Medicamentos de venta libre"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Medicamentos"
        category_id = data["category_id"]
    
    def test_create_category_as_admin(self):
        """Test de crear categoría como admin"""
        response = client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Vitaminas",
                "description": "Suplementos vitamínicos"
            }
        )
        assert response.status_code == 201
    
    def test_create_category_as_customer_fails(self):
        """Test de crear categoría como customer (debe fallar)"""
        response = client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "name": "Test Category",
                "description": "Test"
            }
        )
        assert response.status_code == 403
    
    def test_create_duplicate_category(self):
        """Test de crear categoría duplicada"""
        response = client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Medicamentos",
                "description": "Duplicado"
            }
        )
        assert response.status_code == 400
    
    def test_get_categories_public(self):
        """Test de obtener categorías (público)"""
        response = client.get("/api/v1/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_get_category_by_id(self):
        """Test de obtener categoría por ID"""
        response = client.get(f"/api/v1/categories/{category_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == category_id
        assert data["name"] == "Medicamentos"
    
    def test_update_category_as_seller(self):
        """Test de actualizar categoría como seller"""
        response = client.put(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "name": "Medicamentos OTC",
                "description": "Medicamentos sin receta"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Medicamentos OTC"
    
    def test_search_categories(self):
        """Test de búsqueda de categorías"""
        response = client.get("/api/v1/categories?search=Medicamentos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

# =============================================================================
# TESTS DE PRODUCTOS
# =============================================================================

class TestProducts:
    """Tests de gestión de productos"""
    
    def test_create_product_as_admin(self):
        """Test de crear producto como admin"""
        global product_id
        response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "sku": "MED-001",
                "name": "Paracetamol 500mg",
                "description": "Analgésico y antipirético",
                "price": 45.50,
                "image_url": "https://example.com/paracetamol.jpg",
                "stock_count": 100,
                "is_active": True,
                "category_id": category_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Paracetamol 500mg"
        assert float(data["price"]) == 45.50
        product_id = data["product_id"]
    
    def test_create_product_as_seller_fails(self):
        """Test de crear producto como seller (debe fallar)"""
        response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "sku": "MED-002",
                "name": "Test Product",
                "description": "Test",
                "price": 10.00,
                "stock_count": 10
            }
        )
        assert response.status_code == 403
    
    def test_get_products_public(self):
        """Test de obtener productos (público)"""
        response = client.get("/api/v1/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_product_by_id(self):
        """Test de obtener producto por ID"""
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
    
    def test_get_product_by_sku(self):
        """Test de obtener producto por SKU"""
        response = client.get("/api/v1/products/sku/MED-001")
        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == "MED-001"
    
    def test_update_product_as_admin(self):
        """Test de actualizar producto como admin"""
        response = client.put(
            f"/api/v1/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Paracetamol 500mg (Actualizado)",
                "price": 50.00
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "Actualizado" in data["name"]
        assert float(data["price"]) == 50.00
    
    def test_update_product_image_as_seller(self):
        """Test de actualizar imagen como seller"""
        response = client.patch(
            f"/api/v1/products/{product_id}/image",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "image_url": "https://example.com/new-image.jpg"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["image_url"] == "https://example.com/new-image.jpg"
    
    def test_update_stock_as_admin(self):
        """Test de actualizar stock como admin"""
        response = client.patch(
            f"/api/v1/products/{product_id}/stock?quantity=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stock_count"] == 150  # 100 + 50
    
    def test_search_products(self):
        """Test de búsqueda de productos"""
        response = client.get("/api/v1/products?search=Paracetamol")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_filter_products_by_category(self):
        """Test de filtrar productos por categoría"""
        response = client.get(f"/api/v1/products?category_id={category_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

# =============================================================================
# TESTS DE CARRITO Y PEDIDOS
# =============================================================================

class TestCart:
    """Tests de carrito de compras"""
    
    def test_add_to_cart(self):
        """Test de agregar producto al carrito"""
        global cart_item_id
        response = client.post(
            "/api/v1/orders/cart",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "product_id": product_id,
                "quantity": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        assert data["quantity"] == 2
        cart_item_id = data["cart_cache_id"]
    
    def test_get_cart(self):
        """Test de obtener carrito"""
        response = client.get(
            "/api/v1/orders/cart",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_update_cart_item(self):
        """Test de actualizar cantidad en carrito"""
        response = client.put(
            f"/api/v1/orders/cart/{cart_item_id}",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={"quantity": 3}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 3
    
    def test_checkout_cart(self):
        """Test de crear pedido desde carrito"""
        global order_id
        response = client.post(
            "/api/v1/orders/checkout",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_validation"
        assert len(data["items"]) >= 1
        order_id = data["order_id"]
    
    def test_cart_empty_after_checkout(self):
        """Test de que el carrito se vacíe después del checkout"""
        response = client.get(
            "/api/v1/orders/cart",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

class TestOrders:
    """Tests de gestión de pedidos"""
    
    def test_get_my_orders(self):
        """Test de obtener mis pedidos"""
        response = client.get(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_order_by_id(self):
        """Test de obtener pedido por ID"""
        response = client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
    
    def test_get_all_orders_as_seller(self):
        """Test de obtener todos los pedidos como seller"""
        response = client.get(
            "/api/v1/orders/all",
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_order_status_as_seller(self):
        """Test de actualizar estado de pedido como seller"""
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "status": "approved"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
    
    def test_update_order_status_to_shipped(self):
        """Test de actualizar a estado enviado"""
        response = client.put(
            f"/api/v1/orders/{order_id}/status",
            headers={"Authorization": f"Bearer {seller_token}"},
            json={
                "status": "shipped"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shipped"
    
    def test_filter_orders_by_status(self):
        """Test de filtrar pedidos por estado"""
        response = client.get(
            "/api/v1/orders/all?status=shipped",
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(order["status"] == "shipped" for order in data)

# =============================================================================
# TESTS DE ADMINISTRACIÓN
# =============================================================================

class TestAdmin:
    """Tests de funciones administrativas"""
    
    def test_get_dashboard_stats(self):
        """Test de obtener estadísticas del dashboard"""
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_products" in data
        assert "total_orders" in data
        assert data["total_users"] > 0
    
    def test_get_all_users(self):
        """Test de obtener todos los usuarios"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
    
    def test_get_user_by_id(self):
        """Test de obtener usuario por ID"""
        response = client.get(
            "/api/v1/admin/users/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
    
    def test_update_user(self):
        """Test de actualizar usuario"""
        response = client.put(
            "/api/v1/admin/users/2",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "full_name": "Seller Updated",
                "is_active": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Seller Updated"
    
    def test_admin_access_as_customer_fails(self):
        """Test de acceso admin como customer (debe fallar)"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 403
    
    def test_admin_access_as_seller_fails(self):
        """Test de acceso admin como seller (debe fallar)"""
        response = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        assert response.status_code == 403

# =============================================================================
# TESTS DE CLEANUP Y ELIMINACIÓN
# =============================================================================

class TestDeletion:
    """Tests de eliminación de recursos"""
    
    def test_delete_product_as_admin(self):
        """Test de eliminar producto (soft delete)"""
        response = client.delete(
            f"/api/v1/products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        # Verificar que está marcado como inactivo
        response = client.get(f"/api/v1/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
    
    def test_delete_category_with_products_fails(self):
        """Test de eliminar categoría con productos (debe fallar)"""
        response = client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
    
    def test_delete_user(self):
        """Test de eliminar usuario"""
        response = client.delete(
            "/api/v1/admin/users/4",  # newuser creado en test_register
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

# =============================================================================
# TESTS DE VALIDACIÓN Y ERRORES
# =============================================================================

class TestValidation:
    """Tests de validación y manejo de errores"""
    
    def test_invalid_token(self):
        """Test con token inválido"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_missing_token(self):
        """Test sin token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_create_product_invalid_price(self):
        """Test de crear producto con precio inválido"""
        response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "sku": "TEST-001",
                "name": "Test Product",
                "price": -10.00,  # Precio negativo
                "stock_count": 10
            }
        )
        assert response.status_code == 422
    
    def test_get_nonexistent_product(self):
        """Test de obtener producto inexistente"""
        response = client.get("/api/v1/products/99999")
        assert response.status_code == 404
    
    def test_get_nonexistent_category(self):
        """Test de obtener categoría inexistente"""
        response = client.get("/api/v1/categories/99999")
        assert response.status_code == 404
    
    def test_add_invalid_product_to_cart(self):
        """Test de agregar producto inválido al carrito"""
        response = client.post(
            "/api/v1/orders/cart",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={
                "product_id": 99999,
                "quantity": 1
            }
        )
        assert response.status_code == 400

# =============================================================================
# EJECUTAR TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])