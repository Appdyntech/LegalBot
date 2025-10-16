CREATE TABLE IF NOT EXISTS legal_tickets (
    ticket_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255),
    issue_description TEXT,
    assigned_lawyer INT REFERENCES lawyers(lawyer_id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
