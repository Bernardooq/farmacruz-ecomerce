# 📚 Documentación de API - Farmacruz

## Base URL

```
http://localhost:8000/api/v1
```

## 🔐 Autenticación (`/auth`)

### `POST /auth/register`

Registra un nuevo usuario.

* **Body** : `UserCreate`
* **Response** : `User`
* **Auth** : No requiere

### `POST /auth/login`

Login con username y password.

* **Body** : `username`, `password` (form-data)
* **Response** : `{ "access_token": "...", "token_type": "bearer" }`
* **Auth** : No requiere

### `GET /auth/me`

Obtiene información del usuario actual.

* **Response** : `User`
* **Auth** : Bearer Token requerido

---

## 📂 Categorías (`/categories`)

### `GET /categories`

Lista todas las categorías.

* **Query params** : `skip`, `limit`, `search`
* **Response** : `List[Category]`
* **Auth** : Público

### `GET /categories/{category_id}`

Obtiene una categoría específica.

* **Response** : `Category`
* **Auth** : Público

### `POST /categories`

Crea una nueva categoría.

* **Body** : `CategoryCreate`
* **Response** : `Category`
* **Auth** : 🔒 Seller o Admin

### `PUT /categories/{category_id}`

Actualiza una categoría.

* **Body** : `CategoryUpdate`
* **Response** : `Category`
* **Auth** : 🔒 Seller o Admin

### `DELETE /categories/{category_id}`

Elimina una categoría (si no tiene productos).

* **Response** : `{ "message": "..." }`
* **Auth** : 🔒 Seller o Admin

---

## 📦 Productos (`/products`)

### `GET /products`

Lista productos con filtros.

* **Query params** : `skip`, `limit`, `category_id`, `is_active`, `search`
* **Response** : `List[Product]`
* **Auth** : Público

### `GET /products/{product_id}`

Obtiene un producto por ID.

* **Response** : `Product`
* **Auth** : Público

### `GET /products/sku/{sku}`

Obtiene un producto por SKU.

* **Response** : `Product`
* **Auth** : Público

### `POST /products`

Crea un nuevo producto.

* **Body** : `ProductCreate`
* **Response** : `Product`
* **Auth** : 🔒 Admin

### `PUT /products/{product_id}`

Actualiza un producto completo.

* **Body** : `ProductUpdate`
* **Response** : `Product`
* **Auth** : 🔒 Admin

### `DELETE /products/{product_id}`

Elimina un producto (soft delete).

* **Response** : `Product`
* **Auth** : 🔒 Admin

### `PATCH /products/{product_id}/stock`

Ajusta el stock de un producto.

* **Query param** : `quantity` (puede ser negativo)
* **Response** : `Product`
* **Auth** : 🔒 Admin

### `PATCH /products/{product_id}/image` ⭐ NUEVO

Actualiza solo la imagen de un producto.

* **Body** : `{ "image_url": "..." }`
* **Response** : `Product`
* **Auth** : 🔒 Seller o Admin

---

## 🛒 Pedidos y Carrito (`/orders`)

### Carrito

#### `GET /orders/cart`

Ver carrito del usuario actual.

* **Response** : `List[CartCache]`
* **Auth** : 🔒 Usuario autenticado

#### `POST /orders/cart`

Agregar producto al carrito.

* **Body** : `{ "product_id": 1, "quantity": 2 }`
* **Response** : `CartCache`
* **Auth** : 🔒 Usuario autenticado

#### `PUT /orders/cart/{cart_id}`

Actualizar cantidad en el carrito.

* **Body** : `{ "quantity": 3 }`
* **Response** : `CartCache`
* **Auth** : 🔒 Usuario autenticado

#### `DELETE /orders/cart/{cart_id}`

Eliminar item del carrito.

* **Response** : `{ "message": "..." }`
* **Auth** : 🔒 Usuario autenticado

#### `DELETE /orders/cart`

Limpiar todo el carrito.

* **Response** : `{ "message": "..." }`
* **Auth** : 🔒 Usuario autenticado

### Pedidos

#### `POST /orders/checkout`

Crear pedido desde el carrito.

* **Response** : `Order`
* **Auth** : 🔒 Usuario autenticado

#### `GET /orders`

Mis pedidos.

* **Query params** : `skip`, `limit`, `status`
* **Response** : `List[Order]`
* **Auth** : 🔒 Usuario autenticado

#### `GET /orders/all`

Todos los pedidos (para gestión).

* **Query params** : `skip`, `limit`, `status`
* **Response** : `List[Order]`
* **Auth** : 🔒 Seller o Admin

#### `GET /orders/{order_id}`

Ver un pedido específico.

* **Response** : `Order`
* **Auth** : 🔒 Usuario autenticado (propio) o Seller/Admin

#### `PUT /orders/{order_id}/status`

Actualizar estado de un pedido.

* **Body** : `OrderUpdate`
* **Response** : `Order`
* **Auth** : 🔒 Seller o Admin

#### `POST /orders/{order_id}/cancel`

Cancelar un pedido.

* **Response** : `Order`
* **Auth** : 🔒 Usuario autenticado (propio) o Seller/Admin

---

## 👥 Administración (`/admin`)

### `GET /admin/users`

Lista todos los usuarios.

* **Query params** : `skip`, `limit`
* **Response** : `List[User]`
* **Auth** : 🔒 Admin

### `GET /admin/users/{user_id}`

Obtiene un usuario específico.

* **Response** : `User`
* **Auth** : 🔒 Admin

### `PUT /admin/users/{user_id}`

Actualiza un usuario.

* **Body** : `UserUpdate`
* **Response** : `User`
* **Auth** : 🔒 Admin

### `DELETE /admin/users/{user_id}`

Elimina un usuario.

* **Response** : `{ "message": "..." }`
* **Auth** : 🔒 Admin

### `GET /admin/dashboard`

Estadísticas del sistema.

* **Response** : `DashboardStats`
* **Auth** : 🔒 Admin

---

## 🔑 Roles y Permisos

### Customer (Cliente)

* ✅ Ver productos y categorías
* ✅ Gestionar su carrito
* ✅ Crear y ver sus pedidos
* ✅ Cancelar sus propios pedidos (si están pendientes)

### Seller (Vendedor)

* ✅ Todo lo del Customer
* ✅ **Crear y editar categorías** ⭐
* ✅ **Actualizar imágenes de productos** ⭐
* ✅ Ver todos los pedidos
* ✅ Actualizar estado de pedidos
* ✅ Cancelar cualquier pedido

### Admin (Administrador)

* ✅ Todo lo del Seller
* ✅ CRUD completo de productos
* ✅ Ajustar stock de productos
* ✅ Gestionar usuarios
* ✅ Ver estadísticas del sistema

---

## 📊 Schemas Principales

### UserCreate

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "role": "admin|seller|customer"
}
```

### CategoryCreate

```json
{
  "name": "string",
  "description": "string"
}
```

### ProductCreate

```json
{
  "sku": "string",
  "name": "string",
  "description": "string",
  "price": 99.99,
  "image_url": "string",
  "stock_count": 100,
  "is_active": true,
  "category_id": 1
}
```

### OrderStatus

* `pending_validation` - Pendiente de validación
* `approved` - Aprobado
* `shipped` - Enviado
* `delivered` - Entregado
* `cancelled` - Cancelado

---

## 🚀 Testing rápido con cURL

```bash
# 1. Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# 2. Usar token (guardar el access_token)
TOKEN="tu_access_token_aqui"

# 3. Crear categoría
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Analgésicos", "description": "Medicamentos para el dolor"}'

# 4. Actualizar imagen de producto
curl -X PATCH "http://localhost:8000/api/v1/products/1/image" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/nueva-imagen.jpg"}'
```
