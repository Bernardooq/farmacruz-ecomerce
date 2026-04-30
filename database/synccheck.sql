-- =====================================================
-- synccheck.sql
-- Consultas para verificar los últimos 10 registros 
-- actualizados (o creados) de cada tabla (Vista compacta).
-- =====================================================

-- 1. Tablas que tienen 'updated_at'
SELECT 'users' AS tabla, user_id, username, role, updated_at FROM users ORDER BY updated_at DESC LIMIT 10;

SELECT 'customers' AS tabla, customer_id, username, email, updated_at FROM customers ORDER BY updated_at DESC LIMIT 10;

SELECT 'categories' AS tabla, category_id, name, updated_at FROM categories ORDER BY updated_at DESC LIMIT 10;

SELECT 'products' AS tabla, product_id, substring(name for 30) as name, base_price, stock_count, updated_at FROM products ORDER BY updated_at DESC LIMIT 10;

SELECT 'pricelists' AS tabla, price_list_id, list_name, updated_at FROM pricelists ORDER BY updated_at DESC LIMIT 10;

SELECT 'pricelistitems' AS tabla, price_list_id, product_id, final_price, updated_at FROM pricelistitems ORDER BY updated_at DESC LIMIT 10;

SELECT 'cartcache' AS tabla, customer_id, product_id, quantity, updated_at FROM cartcache ORDER BY updated_at DESC LIMIT 10;

SELECT 'tickets' AS tabla, ticket_id, substring(title for 30) as title, status, updated_at FROM tickets ORDER BY updated_at DESC LIMIT 10;

-- 2. Tablas que no tienen 'updated_at' pero sí 'created_at' o similares
SELECT 'salesgroups' AS tabla, sales_group_id, group_name, created_at FROM salesgroups ORDER BY created_at DESC LIMIT 10;

SELECT 'orders' AS tabla, order_id, customer_id, status, total_amount, created_at FROM orders ORDER BY created_at DESC LIMIT 10;

SELECT 'product_recommendations' AS tabla, product_id, recommended_product_id, score, created_at FROM product_recommendations ORDER BY created_at DESC LIMIT 10;

SELECT 'ticket_messages' AS tabla, message_id, ticket_id, sender_id, created_at FROM ticket_messages ORDER BY created_at DESC LIMIT 10;

SELECT 'groupmarketingmanagers' AS tabla, sales_group_id, marketing_id, assigned_at FROM groupmarketingmanagers ORDER BY assigned_at DESC LIMIT 10;

SELECT 'groupsellers' AS tabla, sales_group_id, seller_id, assigned_at FROM groupsellers ORDER BY assigned_at DESC LIMIT 10;
