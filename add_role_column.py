"""
Database Migration Script
Adds the 'role' column to the 'users' table if it doesn't exist.
Run this script once to update your database schema.

Usage:
    python add_role_column.py
"""
from sqlalchemy import create_engine, text
from config.environment import db_URI

def add_role_column():
    """Add role column to users table if it doesn't exist"""
    engine = create_engine(db_URI)
    
    with engine.connect() as conn:
        # Check if role column exists (PostgreSQL)
        if 'postgresql' in db_URI.lower():
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            """)
        # Check if role column exists (SQLite)
        elif 'sqlite' in db_URI.lower():
            check_query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            # For SQLite, we'll just try to add the column
            try:
                alter_query = text("""
                    ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'customer'
                """)
                conn.execute(alter_query)
                conn.commit()
                print("✓ Successfully added 'role' column to 'users' table (SQLite)")
                return
            except Exception as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    print("✓ 'role' column already exists in 'users' table")
                    return
                else:
                    raise
        
        result = conn.execute(check_query)
        row = result.fetchone()
        
        if row:
            print("✓ 'role' column already exists in 'users' table")
        else:
            # Add role column with default value
            if 'postgresql' in db_URI.lower():
                alter_query = text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(20) DEFAULT 'customer'
                """)
            else:
                alter_query = text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(20) DEFAULT 'customer'
                """)
            
            conn.execute(alter_query)
            conn.commit()
            print("✓ Successfully added 'role' column to 'users' table")

if __name__ == "__main__":
    try:
        add_role_column()
        print("\n✓ Database migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nNote: If the column already exists, you can ignore this error.")
        print("The application should work with the nullable role column.")

