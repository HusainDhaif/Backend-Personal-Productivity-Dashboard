"""
Database Migration Script
Adds the 'role' column to the 'users' table if it doesn't exist.
Run this script once to update your database schema.

Usage:
    python migrations/add_role_column.py
"""
from sqlalchemy import create_engine, text
from config.environment import db_URI

def add_role_column():
    """Add role column to users table if it doesn't exist"""
    engine = create_engine(db_URI)
    
    with engine.connect() as conn:
        try:
            # Check if role column exists (PostgreSQL)
            if 'postgresql' in db_URI.lower() or 'postgres' in db_URI.lower():
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='role'
                """)
                
                result = conn.execute(check_query)
                row = result.fetchone()
                
                if row:
                    print("✓ 'role' column already exists in 'users' table")
                else:
                    # Add role column with default value
                    alter_query = text("""
                        ALTER TABLE users 
                        ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL
                    """)
                    
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Successfully added 'role' column to 'users' table")
                    
                    # Update existing rows
                    update_query = text("""
                        UPDATE users 
                        SET role = 'CUSTOMER' 
                        WHERE role IS NULL
                    """)
                    conn.execute(update_query)
                    conn.commit()
                    print("✓ Updated existing users with default role")
            else:
                # SQLite or other databases
                try:
                    alter_query = text("""
                        ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER'
                    """)
                    conn.execute(alter_query)
                    conn.commit()
                    print("✓ Successfully added 'role' column to 'users' table")
                except Exception as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        print("✓ 'role' column already exists in 'users' table")
                    else:
                        raise
                        
        except Exception as e:
            print(f"✗ Error: {e}")
            raise

if __name__ == "__main__":
    try:
        add_role_column()
        print("\n✓ Database migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nNote: If the column already exists, you can ignore this error.")

