-- Migration script to add 'role' column to 'users' table
-- Run this script on your PostgreSQL database

-- Add role column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'role'
    ) THEN
        ALTER TABLE users 
        ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL;
        
        -- Update existing rows to have 'CUSTOMER' role
        UPDATE users 
        SET role = 'CUSTOMER' 
        WHERE role IS NULL;
        
        RAISE NOTICE 'Role column added successfully';
    ELSE
        RAISE NOTICE 'Role column already exists';
    END IF;
END $$;

