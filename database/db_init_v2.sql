-- ============================================
-- FARMACRUZ - DATABASE SCHEMA v2.1 - CUSTOMERS SEPARATED
-- Sistema de Gestión de Pedidos con Grupos de Ventas
-- ============================================
--
-- CAMBIOS v2.1:
-- - Users: Solo para usuarios internos (admin, marketing, seller)
-- - Customers: Nueva tabla para clientes (separada de Users)
-- - CustomerInfo: Ahora referencia a Customers
-- - Orders y CartCache: Ahora referencian a Customers
--
-- LISTAS DE PRECIOS DINÁMICAS:
-- - PriceLists: Define el nombre y markup por defecto
-- - PriceListItems: Define markup específico por producto
-- ============================================

--- TIPOS ENUM ---

-- Roles solo para usuarios internos (quitamos 'customer')
CREATE TYPE user_role AS ENUM ('admin', 'marketing', 'seller');

CREATE TYPE order_status AS ENUM (
    'pending_validation',
    'assigned',
    'approved',
    'shipped',
    'delivered',
    'cancelled'
);

--- TABLAS PRINCIPALES ---

-- Usuarios del sistema (SOLO INTERNOS: admin, marketing, seller)
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clientes (SEPARADO de Users)
CREATE TABLE Customers (
    customer_id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Grupos de ventas
CREATE TABLE SalesGroups (
    sales_group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Marketing managers asignados a grupos (N:M)
CREATE TABLE GroupMarketingManagers (
    group_marketing_id SERIAL PRIMARY KEY,
    sales_group_id INTEGER NOT NULL REFERENCES SalesGroups (sales_group_id) ON DELETE CASCADE,
    marketing_id INTEGER NOT NULL REFERENCES Users (user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (sales_group_id, marketing_id)
);

-- Vendedores asignados a grupos (N:M)
CREATE TABLE GroupSellers (
    group_seller_id SERIAL PRIMARY KEY,
    sales_group_id INTEGER NOT NULL REFERENCES SalesGroups (sales_group_id) ON DELETE CASCADE,
    seller_id INTEGER NOT NULL REFERENCES Users (user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (sales_group_id, seller_id)
);

-- Categorías de productos
CREATE TABLE Categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Productos
CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    iva_percentage NUMERIC(5, 2) DEFAULT 0.00,
    image_url VARCHAR(255),
    stock_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    category_id INTEGER REFERENCES Categories (category_id)
);

-- Listas de precios (contenedor)
CREATE TABLE PriceLists (
    price_list_id INTEGER PRIMARY KEY,
    list_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Markup específico por producto en cada lista
CREATE TABLE PriceListItems (
    price_list_item_id SERIAL PRIMARY KEY,
    price_list_id INTEGER NOT NULL REFERENCES PriceLists (price_list_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES Products (product_id) ON DELETE CASCADE,
    markup_percentage NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (price_list_id, product_id)
);

-- Información de clientes (AHORA REFERENCIA A CUSTOMERS)
CREATE TABLE CustomerInfo (
    customer_info_id SERIAL PRIMARY KEY,
    customer_id INTEGER UNIQUE NOT NULL REFERENCES Customers (customer_id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    rfc VARCHAR(13),
    sales_group_id INTEGER REFERENCES SalesGroups (sales_group_id),
    price_list_id INTEGER REFERENCES PriceLists (price_list_id),
    address_1 TEXT,
    address_2 TEXT,
    address_3 TEXT
);

-- Pedidos (AHORA REFERENCIA A CUSTOMERS)
CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES Customers (customer_id),
    assigned_seller_id INTEGER REFERENCES Users (user_id),
    assigned_by_user_id INTEGER REFERENCES Users (user_id),
    status order_status NOT NULL DEFAULT 'pending_validation',
    total_amount NUMERIC(12, 2) DEFAULT 0.00,
    shipping_address_number INTEGER CHECK (
        shipping_address_number BETWEEN 1 AND 3
    ),
    assignment_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_at TIMESTAMPTZ,
    validated_at TIMESTAMPTZ
);

-- Items de pedidos
CREATE TABLE OrderItems (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES Orders (order_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES Products (product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    base_price NUMERIC(10, 2) NOT NULL,
    markup_percentage NUMERIC(5, 2) NOT NULL,
    iva_percentage NUMERIC(5, 2) NOT NULL,
    final_price NUMERIC(10, 2) NOT NULL
);

-- Carrito de compras (AHORA REFERENCIA A CUSTOMERS)
CREATE TABLE CartCache (
    cart_cache_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES Customers (customer_id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES Products (product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (customer_id, product_id)
);

--- ÍNDICES PARA OPTIMIZACIÓN ---

CREATE INDEX idx_users_username ON Users (username);

CREATE INDEX idx_users_role ON Users (role);

CREATE INDEX idx_customers_username ON Customers (username);

CREATE INDEX idx_customers_email ON Customers (email);

CREATE INDEX idx_products_sku ON Products (sku);

CREATE INDEX idx_products_category ON Products (category_id);

CREATE INDEX idx_products_active ON Products (is_active);

CREATE INDEX idx_orders_customer ON Orders (customer_id);

CREATE INDEX idx_orders_seller ON Orders (assigned_seller_id);

CREATE INDEX idx_orders_status ON Orders (status);

CREATE INDEX idx_orders_created ON Orders (created_at);

CREATE INDEX idx_orderitems_order ON OrderItems (order_id);

CREATE INDEX idx_orderitems_product ON OrderItems (product_id);

CREATE INDEX idx_cart_customer ON CartCache (customer_id);

CREATE INDEX idx_groupmarketing_group ON GroupMarketingManagers (sales_group_id);

CREATE INDEX idx_groupmarketing_user ON GroupMarketingManagers (marketing_id);

CREATE INDEX idx_groupsellers_group ON GroupSellers (sales_group_id);

CREATE INDEX idx_groupsellers_user ON GroupSellers (seller_id);

CREATE INDEX idx_customerinfo_customer ON CustomerInfo (customer_id);

CREATE INDEX idx_customerinfo_group ON CustomerInfo (sales_group_id);

CREATE INDEX idx_customerinfo_pricelist ON CustomerInfo (price_list_id);

CREATE INDEX idx_pricelistitems_list ON PriceListItems (price_list_id);

CREATE INDEX idx_pricelistitems_product ON PriceListItems (product_id);