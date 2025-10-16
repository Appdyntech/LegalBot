-- =========================
-- ✅ LegalBOT initial DB schema
-- =========================

-- Chat History
CREATE TABLE IF NOT EXISTS legal_chat_history (
    chat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT,
    answer TEXT,
    confidence_score FLOAT,
    model_used VARCHAR(100),
    input_mode VARCHAR(50),
    knowledge_base VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Lawyers
CREATE TABLE IF NOT EXISTS lawyers (
    lawyer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    specialization VARCHAR(255),
    bar_registration_number VARCHAR(100),
    experience_years INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tickets
CREATE TABLE IF NOT EXISTS legal_tickets (
    ticket_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    issue_description TEXT,
    assigned_lawyer INT REFERENCES lawyers(lawyer_id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
