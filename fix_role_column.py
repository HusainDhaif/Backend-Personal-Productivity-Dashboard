"""
Fix Role Column Script
Adds the 'role' column to the 'users' table in PostgreSQL.
Run this script to fix the database schema issue.

Usage:
    python fix_role_column.py
"""
from sqlalchemy import create_engine, text
from config.environment import db_URI

def fix_role_column():
    """Add role column to users table if it doesn't exist"""
    engine = create_engine(db_URI)
    
    with engine.connect() as conn:
        try:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if role column exists (PostgreSQL)
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users' 
                    AND column_name = 'role'
                """)
                
                result = conn.execute(check_query)
                row = result.fetchone()
                
                if row:
                    print("✓ 'role' column already exists in 'users' table")
                    trans.commit()
                else:
                    print("Adding 'role' column to 'users' table...")
                    
                    # Add role column with default value
                    alter_query = text("""
                        ALTER TABLE users 
                        ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL
                    """)
                    
                    conn.execute(alter_query)
                    
                    # Update existing rows to have 'CUSTOMER' role
                    update_query = text("""
                        UPDATE users 
                        SET role = 'CUSTOMER' 
                        WHERE role IS NULL
                    """)
                    conn.execute(update_query)
                    
                    trans.commit()
                    print("✓ Successfully added 'role' column to 'users' table")
                    print("✓ Updated existing users with default role 'CUSTOMER'")
                    
            except Exception as e:
                trans.rollback()
                raise e
                
        except Exception as e:
            print(f"✗ Error: {e}")
            print(f"Error type: {type(e).__name__}")
            raise

if __name__ == "__main__":
    try:
        print("Starting database migration...")
        fix_role_column()
        print("\n✓ Database migration completed successfully!")
        print("You can now restart your FastAPI server.")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nPlease check your database connection and try again.")
        print("You may need to run this SQL manually:")
        print("  ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL;")

