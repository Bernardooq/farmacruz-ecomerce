# 🔒 Restricción de Costo de Envío - Solo Admin/Marketing

## 📋 Problema Resuelto

Los clientes NO deben poder editar el costo de envío. Solo administradores y marketing pueden modificarlo.

---

## ✅ Cambios Implementados

### Frontend

#### 1. CartSummary.jsx ✅
- **ELIMINADO**: Input de costo de envío
- **RESULTADO**: Los clientes solo ven el subtotal y total
- El costo de envío se aplica automáticamente en el backend

**Antes:**
```jsx
<div className="cart-summary-card__row">
  <span>Costo de Envío:</span>
  <input type="number" ... />
</div>
```

**Después:**
```jsx
// Sin input de costo de envío
// Solo muestra Subtotal y Total
```

#### 2. Cart.jsx ✅
- **ELIMINADO**: Estado `shippingCost`
- **ELIMINADO**: Parámetro `shippingCost` en `handleCheckoutClick`
- **ACTUALIZADO**: `checkout()` ya no recibe `shippingCost`

#### 3. CartContext.jsx ✅
- **ACTUALIZADO**: Método `checkout()` ya no acepta `shippingCost`
- **RESULTADO**: El checkout solo envía `shippingAddressNumber`

#### 4. orderService.js ✅
- **ACTUALIZADO**: Método `checkout()` ya no envía `shipping_cost`
- **RESULTADO**: El request solo incluye `shipping_address_number`

#### 5. ModalCreateOrder.jsx y ModalEditOrder.jsx ✅
- **MANTENIDO**: Input de costo de envío (solo para admin/marketing)
- **VALIDACIÓN**: Solo números y 2 decimales
- **PREVIEW**: Cálculo automático del total en tiempo real

---

### Backend

#### 1. routes/orders.py ✅

**Endpoint: POST /orders/checkout**
- **ELIMINADO**: `shipping_cost` del `CheckoutRequest`
- **AGREGADO**: Costo de envío por defecto de **100.00 MXN**
- **LÓGICA**: Los clientes siempre pagan 100 MXN de envío

```python
# ANTES
class CheckoutRequest(BaseModel):
    shipping_address_number: int = 1
    shipping_cost: float = 0.00  # Cliente podía modificar

# DESPUÉS
class CheckoutRequest(BaseModel):
    shipping_address_number: int = 1
    # shipping_cost removido

# En el endpoint:
default_shipping_cost = Decimal("100.00")  # Costo fijo para clientes
order = create_order_from_cart(
    db, 
    customer_id=customer_id, 
    shipping_address_number=checkout_data.shipping_address_number,
    shipping_cost=default_shipping_cost  # Aplicado automáticamente
)
```

**Endpoints: POST /orders/create-for-customer y PUT /orders/{id}/edit**
- **MANTENIDO**: Parámetro `shipping_cost` editable
- **RESTRICCIÓN**: Solo admin y marketing pueden usar estos endpoints
- **VALIDACIÓN**: Ya existe en el backend (verificación de roles)

---

## 🎯 Flujos Actualizados

### 1. Cliente crea orden desde carrito ✅
```
Cliente hace checkout
  ↓
Frontend envía: { shipping_address_number: 1 }
  ↓
Backend aplica: shipping_cost = 100.00 MXN (automático)
  ↓
Order creada con shipping_cost = 100.00
  ↓
total_amount = items + 100.00
```

### 2. Admin/Marketing crea orden directa ✅
```
Admin/Marketing ingresa shipping_cost en ModalCreateOrder
  ↓
Frontend envía: { shipping_cost: X }
  ↓
Backend usa el valor especificado
  ↓
Order creada con shipping_cost = X
  ↓
total_amount = items + X
```

### 3. Admin/Marketing edita orden ✅
```
Admin/Marketing modifica shipping_cost en ModalEditOrder
  ↓
Frontend envía: { shipping_cost: X }
  ↓
Backend actualiza el valor
  ↓
Order actualizada con nuevo shipping_cost = X
  ↓
total_amount recalculado = items + X
```

---

## 🔐 Permisos por Rol

| Rol | Puede ver shipping_cost | Puede editar shipping_cost |
|-----|------------------------|---------------------------|
| **Cliente** | ❌ No (oculto) | ❌ No (100 MXN automático) |
| **Seller** | ✅ Sí (solo lectura) | ❌ No |
| **Marketing** | ✅ Sí | ✅ Sí (crear/editar órdenes) |
| **Admin** | ✅ Sí | ✅ Sí (crear/editar órdenes) |

---

## ⚙️ Configuración del Costo de Envío

### Costo por Defecto para Clientes

El costo de envío por defecto está definido en `backend/farmacruz_api/routes/orders.py`:

```python
default_shipping_cost = Decimal("100.00")  # 100 MXN
```

**Para cambiar el costo por defecto:**
1. Editar el archivo `backend/farmacruz_api/routes/orders.py`
2. Buscar la línea `default_shipping_cost = Decimal("100.00")`
3. Cambiar el valor (ej: `Decimal("150.00")` para 150 MXN)
4. Reiniciar el servidor backend

**Alternativa (recomendada):**
Mover este valor a una variable de entorno en `.env`:

```python
# En .env
DEFAULT_SHIPPING_COST=100.00

# En routes/orders.py
from core.config import settings
default_shipping_cost = Decimal(str(settings.DEFAULT_SHIPPING_COST))
```

---

## 📦 Archivos Modificados

### Frontend (5 archivos)
1. ✅ `react/src/components/cart/CartSummary.jsx` - Eliminado input
2. ✅ `react/src/pages/Cart.jsx` - Eliminado manejo de shipping_cost
3. ✅ `react/src/context/CartContext.jsx` - Actualizado checkout()
4. ✅ `react/src/services/orderService.js` - Actualizado checkout()
5. ✅ `react/src/components/modals/orders/ModalCreateOrder.jsx` - Mantenido (admin/marketing)
6. ✅ `react/src/components/modals/orders/ModalEditOrder.jsx` - Mantenido (admin/marketing)

### Backend (1 archivo)
1. ✅ `backend/farmacruz_api/routes/orders.py` - Aplicar costo por defecto

---

## 🧪 Testing

### Pruebas Requeridas

#### Como Cliente:
- [ ] Agregar productos al carrito
- [ ] Ir a checkout
- [ ] Verificar que NO aparece input de costo de envío
- [ ] Confirmar pedido
- [ ] Verificar en detalles que shipping_cost = 100.00 MXN
- [ ] Verificar que total = subtotal + 100.00

#### Como Admin/Marketing:
- [ ] Crear orden directa para cliente
- [ ] Ingresar costo de envío personalizado (ej: 150.00)
- [ ] Verificar preview del total en tiempo real
- [ ] Guardar orden
- [ ] Verificar que shipping_cost = 150.00
- [ ] Editar orden existente
- [ ] Cambiar costo de envío
- [ ] Verificar que se actualiza correctamente

#### Como Seller:
- [ ] Ver detalles de orden
- [ ] Verificar que se muestra shipping_cost (solo lectura)
- [ ] Intentar editar orden (debe fallar - sin permisos)

---

## 💡 Notas Importantes

1. **Costo fijo para clientes**: Todos los clientes pagan 100 MXN de envío por defecto
2. **Sin input visible**: Los clientes no ven ni pueden modificar el costo de envío
3. **Admin/Marketing tienen control total**: Pueden especificar cualquier costo al crear/editar órdenes
4. **Sellers solo lectura**: Pueden ver el costo pero no modificarlo
5. **Backward compatible**: Órdenes antiguas mantienen su shipping_cost original

---

## 🚀 Deployment

### 1. Frontend
```bash
cd react
npm run build
# Subir dist/ a S3/CloudFront
```

### 2. Backend
```bash
# En el servidor EC2
cd ~/farmacruz-ecomerce/backend
git pull origin main
sudo systemctl restart farmacruz-api
```

### 3. Verificar
- [ ] Cliente no puede editar shipping_cost
- [ ] Checkout aplica 100 MXN automáticamente
- [ ] Admin/Marketing pueden editar shipping_cost
- [ ] Sellers solo ven shipping_cost (lectura)

---

## ✅ Resultado Final

- ✅ Clientes NO pueden modificar el costo de envío
- ✅ Costo de envío por defecto: 100.00 MXN
- ✅ Admin/Marketing pueden especificar costo personalizado
- ✅ Sellers solo visualización (sin edición)
- ✅ Preview del total en tiempo real para admin/marketing
- ✅ Validación de entrada numérica (solo números, 2 decimales)

**¡Restricción implementada correctamente! 🔒**
