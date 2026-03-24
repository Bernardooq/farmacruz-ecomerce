-- =====================================================
-- MIGRATION: Support Tickets System
-- Run this script to add ticketing capabilities to an existing DB
-- =====================================================

-- 1. TABLA: tickets
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'cancelled', 'escalated')),
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    creator_id INTEGER NOT NULL,
    creator_type VARCHAR(50) NOT NULL CHECK (creator_type IN ('customer', 'user')),
    assigned_to INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_creator ON tickets (creator_id, creator_type);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets (assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);

-- 2. TABLA: ticket_messages
CREATE TABLE IF NOT EXISTS ticket_messages (
    message_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    sender_id INTEGER NOT NULL,
    sender_type VARCHAR(50) NOT NULL CHECK (sender_type IN ('customer', 'user')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket ON ticket_messages (ticket_id);
