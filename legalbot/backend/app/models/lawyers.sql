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
