"""
Database Initialization Script
Creates all required tables if they don't exist.
Also adds missing columns like 'role' to users table.

Usage:
    python init_database.py
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError
from config.environment import db_URI
from models.base import Base
from models.user import UserModel
from models.task import TaskModel
from models.habit import HabitModel
from models.daily_goal import DailyGoalModel
from models.note import NoteModel

def init_database():
    """Initialize database with all tables and required columns"""
    print("Connecting to database...")
    engine = create_engine(db_URI)
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            print("Creating all tables...")
            # Create all tables
            Base.metadata.create_all(bind=engine)
            print("✓ All tables created/verified")
            
            # Check and add role column to users table if missing
            print("Checking users table for 'role' column...")
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            if 'users' in table_names:
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                if 'role' not in columns:
                    print("Adding 'role' column to users table...")
                    try:
                        conn.execute(text("""
                            ALTER TABLE users 
                            ADD COLUMN role VARCHAR(50) DEFAULT 'CUSTOMER' NOT NULL
                        """))
                        
                        # Update existing rows
                        conn.execute(text("""
                            UPDATE users 
                            SET role = 'CUSTOMER' 
                            WHERE role IS NULL
                        """))
                        
                        print("✓ 'role' column added to users table")
                    except Exception as e:
                        print(f"Note: {e}")
                else:
                    print("✓ 'role' column already exists")
            else:
                print("✓ Users table will be created with role column")
            
            trans.commit()
            print("\n✓ Database initialization completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error during initialization: {e}")
            raise

if __name__ == "__main__":
    try:
        init_database()
        print("\nDatabase is ready!")
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        print("\nPlease check your database connection and try again.")

