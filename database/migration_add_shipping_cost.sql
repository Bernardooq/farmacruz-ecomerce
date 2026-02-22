-- =====================================================
-- Migration: Add shipping_cost to orders table
-- Date: 2026-02-21
-- Description: Adds shipping_cost field to track delivery costs
-- =====================================================

-- Add shipping_cost column to orders table
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS shipping_cost NUMERIC(10, 2) DEFAULT 0.00;

-- Update existing orders to have 0.00 shipping cost
UPDATE orders 
SET shipping_cost = 0.00 
WHERE shipping_cost IS NULL;

-- Add comment to document the field
COMMENT ON COLUMN orders.shipping_cost IS 'Costo de envío del pedido en pesos mexicanos';

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    column_default, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'orders' 
AND column_name = 'shipping_cost';
