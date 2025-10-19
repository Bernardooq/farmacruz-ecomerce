
--- 1. CREACIÓN DE TIPOS PERSONALIZADOS ---
-- Define los roles de usuario permitidos
CREATE TYPE user_role AS ENUM (
  'admin',
  'seller',
  'customer'
);

-- Estados de pedido permitidos
CREATE TYPE order_status AS ENUM (
  'cart',                   -- El pedido esta en el carrito del cliente, no es visible para el vendedor.
  'pending_validation',     -- El cliente ha enviado el pedido, esperando aprobacion del vendedor.
  'approved',               -- El vendedor ha aprobado el pedido.
  'shipped',                -- El pedido ha sido enviado.
  'cancelled'               -- El pedido ha sido cancelado (por el admin o vendedor).
);

--- 2. CREACION DE TABLAS ---
-- Tabla para todos los usuarios (Administradores, Vendedores, Clientes)
CREATE TABLE Users (
  user_id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  role user_role NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para categorias de productos
CREATE TABLE Categories (
  category_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT
);

-- Tabla para los productos (sincronizados desde el ERP)
CREATE TABLE Products (
  product_id SERIAL PRIMARY KEY,
  sku VARCHAR(100) UNIQUE NOT NULL, -- Clave de enlace con Alpha ERP
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
  image_url VARCHAR(255),
  stock_count INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true,
  category_id INTEGER,
  
  FOREIGN KEY (category_id) REFERENCES Categories(category_id)
);

-- Tabla con informacion de la empresa cliente (farmacia)
CREATE TABLE CustomerInfo (
  customer_info_id SERIAL PRIMARY KEY,
  user_id INTEGER UNIQUE NOT NULL, -- El usuario de tipo customer
  business_name VARCHAR(255) NOT NULL,
  address TEXT,
  rfc VARCHAR(13),
  
  FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Tabla para la cabecera de los pedidos
CREATE TABLE Orders (
  order_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL, -- El cliente que hizo el pedido
  seller_id INTEGER, -- El vendedor que debe validar
  status order_status NOT NULL DEFAULT 'cart',
  total_amount NUMERIC(12, 2) DEFAULT 0.00,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  validated_at TIMESTAMP WITH TIME ZONE, -- Se llena cuando el vendedor aprueba
  
  FOREIGN KEY (user_id) REFERENCES Users(user_id),
  FOREIGN KEY (seller_id) REFERENCES Users(user_id)
);

-- Tabla para el detalle de los productos en cada pedido
CREATE TABLE OrderItems (
  order_item_id SERIAL PRIMARY KEY,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  price_at_purchase NUMERIC(10, 2) NOT NULL, -- Guarda el precio al momento de la compra
  
  FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- --- 3. CREACION DE INDICES ---
-- Mayor velocidad en las busquedas
CREATE INDEX idx_products_sku ON Products(sku);
CREATE INDEX idx_orders_user_id ON Orders(user_id);
CREATE INDEX idx_orders_seller_id ON Orders(seller_id);
CREATE INDEX idx_orderitems_order_id ON OrderItems(order_id);