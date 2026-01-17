-- =====================================================
-- FarmaCruz Database Initialization Script v2
-- =====================================================

-- Eliminar tablas existentes si las hay (cuidado en producción)
DROP TABLE IF EXISTS cartcache CASCADE;
DROP TABLE IF EXISTS orderitems CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS pricelistitems CASCADE;
DROP TABLE IF EXISTS pricelists CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customerinfo CASCADE;
DROP TABLE IF EXISTS groupsellers CASCADE;
DROP TABLE IF EXISTS groupmarketingmanagers CASCADE;
DROP TABLE IF EXISTS salesgroups CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Habilitar extension UUID si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLA: users (Usuarios internos: admin, marketing, seller)
-- =====================================================
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,  -- NO SERIAL - asignado manualmente o por backend
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'marketing', 'seller')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: user_id debe ser positivo
    CONSTRAINT check_user_id_positive CHECK (user_id > 0)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- =====================================================
-- TABLA: customers (Clientes del e-commerce)
-- =====================================================
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- NUEVO: Agente/vendedor asignado desde DBF
    agent_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    
    CONSTRAINT customers_username_unique UNIQUE (username),
    CONSTRAINT customers_email_unique UNIQUE (email)
);

CREATE INDEX idx_customers_username ON customers(username);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_agent_id ON customers(agent_id);

-- =====================================================
-- TABLA: salesgroups (Grupos de ventas)
-- =====================================================
CREATE TABLE salesgroups (
    sales_group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: groupmarketingmanagers (Relación N:M)
-- =====================================================
CREATE TABLE groupmarketingmanagers (
    group_marketing_id SERIAL PRIMARY KEY,
    sales_group_id INTEGER NOT NULL REFERENCES salesgroups(sales_group_id) ON DELETE CASCADE,
    marketing_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_group_marketing UNIQUE (sales_group_id, marketing_id)
);

CREATE INDEX idx_groupmarketingmanagers_group ON groupmarketingmanagers(sales_group_id);
CREATE INDEX idx_groupmarketingmanagers_marketing ON groupmarketingmanagers(marketing_id);

-- =====================================================
-- TABLA: groupsellers (Relación N:M)
-- =====================================================
CREATE TABLE groupsellers (
    group_seller_id SERIAL PRIMARY KEY,
    sales_group_id INTEGER NOT NULL REFERENCES salesgroups(sales_group_id) ON DELETE CASCADE,
    seller_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_group_seller UNIQUE (sales_group_id, seller_id)
);

CREATE INDEX idx_groupsellers_group ON groupsellers(sales_group_id);
CREATE INDEX idx_groupsellers_seller ON groupsellers(seller_id);

-- =====================================================
-- TABLA: categories (Categorías de productos)
-- =====================================================
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: products (Productos del catálogo)
-- =====================================================
CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    codebar VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    descripcion_2 TEXT,
    unidad_medida VARCHAR(10),
    base_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    iva_percentage NUMERIC(5, 2) DEFAULT 0.00,
    image_url VARCHAR(255),
    stock_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    category_id INTEGER REFERENCES categories(category_id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_codebar ON products(codebar);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_category ON products(category_id);

-- =====================================================
-- TABLA: pricelists (Listas de precios)
-- =====================================================
CREATE TABLE pricelists (
    price_list_id INTEGER PRIMARY KEY,
    list_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: pricelistitems (Markup por producto en lista)
-- =====================================================
CREATE TABLE pricelistitems (
    price_list_item_id SERIAL PRIMARY KEY,
    price_list_id INTEGER NOT NULL REFERENCES pricelists(price_list_id) ON DELETE CASCADE,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    markup_percentage NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_pricelist_product UNIQUE (price_list_id, product_id)
);

CREATE INDEX idx_pricelistitems_list ON pricelistitems(price_list_id);
CREATE INDEX idx_pricelistitems_product ON pricelistitems(product_id);

-- =====================================================
-- TABLA: customerinfo (Información comercial de clientes)
-- =====================================================
CREATE TABLE customerinfo (
    customer_info_id SERIAL PRIMARY KEY,
    customer_id INTEGER UNIQUE NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    business_name VARCHAR(255) NOT NULL,
    rfc VARCHAR(13),
    sales_group_id INTEGER REFERENCES salesgroups(sales_group_id),
    price_list_id INTEGER REFERENCES pricelists(price_list_id),
    address_1 TEXT,
    address_2 TEXT,
    address_3 TEXT,
    telefono_1 VARCHAR(15),
    telefono_2 VARCHAR(15)
);

CREATE INDEX idx_customerinfo_customer ON customerinfo(customer_id);
CREATE INDEX idx_customerinfo_group ON customerinfo(sales_group_id);
CREATE INDEX idx_customerinfo_pricelist ON customerinfo(price_list_id);

-- =====================================================
-- TABLA: orders (Pedidos)
-- =====================================================
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    assigned_seller_id INTEGER REFERENCES users(user_id),
    assigned_by_user_id INTEGER REFERENCES users(user_id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending_validation' 
        CHECK (status IN ('pending_validation', 'approved', 'shipped', 'delivered', 'cancelled')),
    total_amount NUMERIC(12, 2) DEFAULT 0.00,
    shipping_address_number INTEGER CHECK (shipping_address_number BETWEEN 1 AND 3),
    assignment_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP WITH TIME ZONE,
    validated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_seller ON orders(assigned_seller_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at);

-- =====================================================
-- TABLA: orderitems (Items de pedidos)
-- =====================================================
CREATE TABLE orderitems (
    order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    base_price NUMERIC(10, 2) NOT NULL,
    markup_percentage NUMERIC(5, 2) NOT NULL,
    iva_percentage NUMERIC(5, 2) NOT NULL,
    final_price NUMERIC(10, 2) NOT NULL
);

CREATE INDEX idx_orderitems_order ON orderitems(order_id);
CREATE INDEX idx_orderitems_product ON orderitems(product_id);

-- =====================================================
-- TABLA: cartcache (Carrito de compras temporal)
-- =====================================================
CREATE TABLE cartcache (
    cart_cache_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_cart_item UNIQUE (customer_id, product_id)
);

CREATE INDEX idx_cartcache_customer ON cartcache(customer_id);
CREATE INDEX idx_cartcache_product ON cartcache(product_id);