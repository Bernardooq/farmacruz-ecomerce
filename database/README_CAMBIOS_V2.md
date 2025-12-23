# FarmaCruz - Cambios en Base de Datos v2.0

## 📋 Resumen de Cambios

Este documento detalla todos los cambios realizados en la estructura de la base de datos para soportar los nuevos requerimientos del sistema.

---

## 🆕 **1. NUEVO ROL: Marketing Manager**

### **Enum Actualizado:**
```sql
CREATE TYPE user_role AS ENUM (
    'admin',
    'marketing',    -- NUEVO
    'seller',
    'customer'
);
```

### **Responsabilidades:**
- Líder de un Grupo de Ventas
- Asigna pedidos a vendedores de su grupo
- Puede cambiar estatus de pedidos
- Gestiona equipo de vendedores

---

## 👥 **2. GRUPOS DE VENTAS**

### **Tabla: `SalesGroups`**
```sql
CREATE TABLE SalesGroups (
    sales_group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    marketing_manager_id INTEGER NOT NULL,  -- Líder del grupo
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Características:**
- Cada grupo tiene **1 Marketing Manager** (líder)
- Un grupo puede tener **N vendedores**
- Solo el **Admin** puede crear grupos

### **Tabla: `GroupSellers`**
```sql
CREATE TABLE GroupSellers (
    group_seller_id SERIAL PRIMARY KEY,
    sales_group_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(seller_id)  -- Un vendedor solo en UN grupo
);
```

**Reglas:**
- Un vendedor solo puede pertenecer a **un grupo a la vez**
- Constraint valida que sea un usuario con rol 'seller'

---

## 🏢 **3. CLIENTES ASIGNADOS A GRUPOS**

### **Modificación en `CustomerInfo`:**
```sql
ALTER TABLE CustomerInfo 
ADD COLUMN sales_group_id INTEGER,
ADD FOREIGN KEY (sales_group_id) REFERENCES SalesGroups(sales_group_id);
```

**Beneficios:**
- Cada cliente pertenece a un grupo específico
- Define qué equipo de ventas lo atiende
- Facilita la distribución de carga de trabajo

---

## 📦 **4. ASIGNACIÓN DE PEDIDOS**

### **Nuevo Estado en Orders:**
```sql
CREATE TYPE order_status AS ENUM (
    'pending_validation',
    'assigned',           -- NUEVO: Pedido asignado a vendedor
    'approved',
    'shipped',
    'delivered',
    'cancelled'
);
```

### **Modificación en `Orders`:**
```sql
ALTER TABLE Orders
ADD COLUMN assigned_seller_id INTEGER,
ADD COLUMN assigned_at TIMESTAMP WITH TIME ZONE,
ADD FOREIGN KEY (assigned_seller_id) REFERENCES Users(user_id);
```

### **Nueva Tabla: `OrderAssignments`**
```sql
CREATE TABLE OrderAssignments (
    assignment_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    assigned_by_user_id INTEGER NOT NULL,    -- Quién asignó
    assigned_to_seller_id INTEGER NOT NULL,  -- A quién se asignó
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);
```

**Flujo de Asignación:**
1. Cliente crea pedido → `status = 'pending_validation'`
2. Marketing/Admin asigna a vendedor → `status = 'assigned'`
3. Vendedor valida/aprueba → `status = 'approved'`

---

## 🧪 **5. PRODUCTOS - NUEVOS CAMPOS**

### **Tabla `Products` Actualizada:**
```sql
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    laboratory VARCHAR(255),                    -- NUEVO: Fabricante
    base_price NUMERIC(10, 2) NOT NULL,        -- NUEVO: Precio base
    iva_percentage NUMERIC(5, 2) DEFAULT 0.00, -- NUEVO: % de IVA
    image_url VARCHAR(255),
    stock_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    category_id INTEGER
);
```

### **Campos Nuevos:**

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `laboratory` | VARCHAR(255) | Fabricante/Laboratorio | "Pfizer", "Bayer" |
| `base_price` | NUMERIC(10,2) | Precio base SIN markup | 100.00 |
| `iva_percentage` | NUMERIC(5,2) | % de IVA | 16.00 (para 16%) |

**Nota:** El campo `price` se renombró a `base_price` para mayor claridad.

---

## 💰 **6. LISTAS DE PRECIOS CON MARKUP**

### **Nueva Tabla: `PriceLists`**
```sql
CREATE TABLE PriceLists (
    price_list_id SERIAL PRIMARY KEY,
    list_name VARCHAR(100) NOT NULL,
    markup_percentage NUMERIC(5, 2) NOT NULL,  -- % de ganancia
    description TEXT,
    is_active BOOLEAN DEFAULT true
);
```

### **Ejemplos de Listas:**
```sql
INSERT INTO PriceLists VALUES
('Lista Estándar', 0.00, 'Sin margen'),
('Lista A - Mayoristas', 4.00, '4% de margen'),
('Lista B - Minoristas', 8.00, '8% de margen'),
('Lista C - Especial', 12.00, '12% de margen');
```

### **Asignación a Clientes:**
```sql
ALTER TABLE CustomerInfo
ADD COLUMN price_list_id INTEGER,
ADD FOREIGN KEY (price_list_id) REFERENCES PriceLists(price_list_id);
```

### **Cálculo de Precio Final:**

```
Precio Base = $100.00
Markup = 4%
IVA = 16%

Paso 1: Aplicar Markup
  Precio con Markup = $100.00 + ($100.00 × 0.04) = $104.00

Paso 2: Calcular IVA sobre precio con markup
  IVA = $104.00 × 0.16 = $16.64

Paso 3: Precio Final
  Total = $104.00 + $16.64 = $120.64
```

### **Función SQL para Cálculo:**
```sql
SELECT * FROM calculate_final_price(
    product_id := 123,
    customer_user_id := 456
);
```

**Retorna:**
- `base_price`: 100.00
- `markup_percentage`: 4.00
- `iva_percentage`: 16.00
- `price_with_markup`: 104.00
- `iva_amount`: 16.64
- `final_price`: 120.64

---

## 📍 **7. MÚLTIPLES DIRECCIONES POR CLIENTE**

### **Nueva Tabla: `CustomerAddresses`**
```sql
CREATE TABLE CustomerAddresses (
    address_id SERIAL PRIMARY KEY,
    customer_info_id INTEGER NOT NULL,
    address_label VARCHAR(50),           -- "Principal", "Sucursal Centro"
    street VARCHAR(255) NOT NULL,
    neighborhood VARCHAR(100),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10),
    country VARCHAR(100) DEFAULT 'México',
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT false
);
```

### **Características:**
- ✅ Hasta **3 direcciones** por cliente
- ✅ Trigger automático que previene más de 3
- ✅ Una puede ser marcada como `is_default`
- ✅ Campos detallados para dirección completa

### **Trigger de Validación:**
```sql
CREATE TRIGGER trigger_check_address_limit
BEFORE INSERT ON CustomerAddresses
FOR EACH ROW
EXECUTE FUNCTION check_address_limit();
```

### **Uso en Pedidos:**
```sql
ALTER TABLE Orders
ADD COLUMN shipping_address_id INTEGER,
ADD FOREIGN KEY (shipping_address_id) REFERENCES CustomerAddresses(address_id);
```

---

## 📊 **8. TABLA OrderItems ACTUALIZADA**

```sql
CREATE TABLE OrderItems (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    base_price NUMERIC(10, 2) NOT NULL,        -- NUEVO: Precio base
    markup_percentage NUMERIC(5, 2) NOT NULL,  -- NUEVO: % aplicado
    iva_percentage NUMERIC(5, 2) NOT NULL,     -- NUEVO: % IVA
    final_price NUMERIC(10, 2) NOT NULL        -- NUEVO: Precio final completo
);
```

**Ventajas:**
- Guarda histórico completo del cálculo
- Permite auditorías
- Muestra desglose de precios

---

## 🔐 **9. PERMISOS Y AUTORIZACIÓN**

### **Matriz de Permisos:**

| Acción | Admin | Marketing | Seller | Customer |
|--------|-------|-----------|--------|----------|
| Crear Grupos | ✅ | ❌ | ❌ | ❌ |
| Asignar Vendedores a Grupo | ✅ | ❌ | ❌ | ❌ |
| Asignar Pedidos | ✅ | ✅* | ❌ | ❌ |
| Cambiar Status Pedido | ✅ | ✅ | ✅** | ❌ |
| Ver Todos los Pedidos | ✅ | ✅*** | ✅**** | ❌ |
| Crear Listas de Precios | ✅ | ❌ | ❌ | ❌ |

**Notas:**
- \* Marketing solo puede asignar a vendedores de **su grupo**
- \** Seller solo puede validar pedidos **asignados a él**
- \*** Marketing solo ve pedidos de **su grupo**
- \**** Seller solo ve pedidos **asignados a él**

---

## 📈 **10. VISTAS Y FUNCIONES ÚTILES**

### **Vista: Precios por Cliente**
```sql
SELECT * FROM vw_customer_product_prices
WHERE customer_user_id = 123;
```

Retorna todos los productos con precio calculado para ese cliente específico.

### **Función: Calcular Precio**
```sql
SELECT * FROM calculate_final_price(product_id, customer_user_id);
```

---

## 🚀 **11. MIGRACIÓN DESDE v1.0**

### **Pasos para Migrar:**

1. **Backup de datos actuales**
2. **Crear nuevas tablas y relaciones**
3. **Migrar datos:**

```sql
-- Migrar precio a base_price
UPDATE Products SET base_price = price;

-- Convertir CustomerInfo.address a CustomerAddresses
INSERT INTO CustomerAddresses (
    customer_info_id, 
    address_label, 
    street,
    city,
    state,
    is_default
)
SELECT 
    customer_info_id,
    'Principal',
    address,
    'Ciudad Desconocida',
    'Estado Desconocido',
    true
FROM CustomerInfo
WHERE address IS NOT NULL;

-- Crear lista de precios por defecto
INSERT INTO PriceLists (list_name, markup_percentage)
VALUES ('Lista Estándar', 0.00);

-- Asignar todos los clientes a lista estándar
UPDATE CustomerInfo 
SET price_list_id = (SELECT price_list_id FROM PriceLists WHERE list_name = 'Lista Estándar');
```

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### **Backend (FastAPI):**
- [ ] Crear modelos Pydantic para nuevas tablas
- [ ] Endpoints para gestión de grupos
- [ ] Endpoints para asignación de pedidos
- [ ] Lógica de cálculo de precios
- [ ] Middleware de autorización por roles
- [ ] CRUD de direcciones de cliente
- [ ] CRUD de listas de precios

### **Frontend (React):**
- [ ] Panel de Admin: Gestión de Grupos
- [ ] Panel de Admin: Gestión de Listas de Precios
- [ ] Panel de Marketing: Ver su grupo
- [ ] Panel de Marketing: Asignar pedidos
- [ ] Panel de Vendedor: Ver pedidos asignados
- [ ] Panel de Cliente: Gestionar direcciones
- [ ] Mostrar precio con markup e IVA en productos
- [ ] Desglose de precio en carrito

### **Database:**
- [x] Crear esquema SQL v2.0
- [ ] Ejecutar en base de datos de desarrollo
- [ ] Ejecutar scripts de migración
- [ ] Verificar constraints y triggers
- [ ] Crear datos de prueba
- [ ] Ejecutar en producción

---

## 📞 **SOPORTE**

Para dudas sobre la implementación, contactar al equipo de desarrollo.
