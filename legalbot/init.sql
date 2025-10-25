-- ===========================
-- ⚖️ LegalBOT Database Schema
-- ===========================

-- Create main database
-- Database already created by Docker (POSTGRES_DB)
\connect legal_chunks_db;


-- ===========================
-- 👥 Customers Table
-- ===========================
-- ===========================
-- 👥 Customers Table (Enhanced)
-- ===========================
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_id UUID DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    location VARCHAR(255),
    google_verified BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    password_hash VARCHAR(255),
    google_id VARCHAR(255),
    auth_provider VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 🧑‍⚖️ Lawyers Table
-- ===========================
CREATE TABLE IF NOT EXISTS lawyers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(255),
    experience_years INT,
    contact_info VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 💬 Chat History Table
-- ===========================
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100),
    user_name VARCHAR(100),
    question TEXT,
    answer TEXT,
    knowledge_base VARCHAR(100),
    model_used VARCHAR(100),
    confidence_score NUMERIC,
    input_mode VARCHAR(50),
    retrieval_mode VARCHAR(50),
    retrieval_time FLOAT,
    input_channel VARCHAR(50),
    confidence NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 🧾 Legal Chat History (Legacy)
-- ===========================
CREATE TABLE IF NOT EXISTS legal_chat_history (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100),
    query TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- 🎟️ Legal Tickets Table
-- ===========================
CREATE TABLE IF NOT EXISTS legal_tickets (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100),
    issue_category VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================
-- ✅ Default Data (Optional)
-- ===========================
INSERT INTO lawyers (name, specialization, experience_years, contact_info)
VALUES
('John Doe', 'Corporate Law', 10, 'john@example.com'),
('Jane Smith', 'Criminal Law', 7, 'jane@example.com')
ON CONFLICT DO NOTHING;
