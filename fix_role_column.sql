-- SQL script to add 'role' column to 'users' table in PostgreSQL
-- Run this script directly on your PostgreSQL database

-- Check if column exists and add it if it doesn't
DO $$ 
BEGIN
    -- Check if role column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'users' 
        AND column_name = 'role'
    ) THEN
        -- Add the role column
        ALTER TABLE users 
        ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL;
        
        -- Update any existing NULL values (shouldn't be any, but just in case)
        UPDATE users 
        SET role = 'CUSTOMER' 
        WHERE role IS NULL;
        
        RAISE NOTICE 'Role column added successfully to users table';
    ELSE
        RAISE NOTICE 'Role column already exists in users table';
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'users' 
AND column_name = 'role';

