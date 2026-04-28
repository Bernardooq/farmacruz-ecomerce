-- =====================================================
-- FarmaCruz Database Live Edit Script
-- Ejecutar estos comandos para actualizar la base de datos de producción
-- SIN afectar los datos existentes ni bloquear el tráfico.
-- =====================================================

-- 1. Habilitar extensión pg_trgm para soporte GIN de ILIKE
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Eliminar índices B-Tree redundantes o inútiles para ILIKE
-- Usamos IF EXISTS por seguridad
DROP INDEX IF EXISTS idx_products_name_search;
DROP INDEX IF EXISTS idx_products_desc2;
DROP INDEX IF EXISTS idx_pricelistitems_composite;

-- 3. Crear índices GIN CONCURRENTLY (Para no bloquear las tablas en producción)
-- Nota IMPORTANTE: CONCURRENTLY no se puede usar dentro de un bloque de transacción (BEGIN/COMMIT).
-- Deben ejecutarse directamente. Esto permite que el sistema siga vendiendo mientras se construyen.

-- Tabla: users
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_full_name_gin ON users USING gin (full_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_gin ON users USING gin (username gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_gin ON users USING gin (email gin_trgm_ops);

-- Tabla: customers
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_full_name_gin ON customers USING gin (full_name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_username_gin ON customers USING gin (username gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_email_gin ON customers USING gin (email gin_trgm_ops);

-- Tabla: salesgroups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_salesgroups_group_name_gin ON salesgroups USING gin (group_name gin_trgm_ops);

-- Tabla: categories
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categories_name_gin ON categories USING gin (name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_categories_description_gin ON categories USING gin (description gin_trgm_ops);

-- Tabla: products
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_product_id_gin ON products USING gin (product_id gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_codebar_gin ON products USING gin (codebar gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_name_gin ON products USING gin (name gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_description_gin ON products USING gin (description gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_descripcion_2_gin ON products USING gin (descripcion_2 gin_trgm_ops);

-- Tabla: customerinfo
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customerinfo_rfc_gin ON customerinfo USING gin (rfc gin_trgm_ops);

-- =====================================================
-- 4. Optimización de Autovacuum para Tablas de Alta Mutación
-- =====================================================
-- Al acelerar el Autovacuum al 5% (en lugar del 20% por defecto), 
-- evitamos la acumulación de Dead Tuples (basura) cuando los carritos 
-- se borran o los pedidos cambian de estatus.
ALTER TABLE orders SET (autovacuum_vacuum_scale_factor = 0.05);
ALTER TABLE cartcache SET (autovacuum_vacuum_scale_factor = 0.05);

-- =====================================================
-- Fin del script de edición en vivo
-- =====================================================
