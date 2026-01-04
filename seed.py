from sqlalchemy.orm import sessionmaker
from models.base import Base
from DATA.user_data import user_list
from config.environment import db_URI
from sqlalchemy import create_engine
from models.daily_goal import DailyGoalModel
from models.task import TaskModel
from models.note import NoteModel
from models.habit import HabitModel 

engine = create_engine(db_URI)
SessionLocal = sessionmaker(bind=engine)

try:
    print("Recreating database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Seeding the database...")
    db = SessionLocal()

    db.add_all(user_list)
    db.commit()

    db.close()

    print("Database seeding complete! 👋")
except Exception as e:
    print("An error occurred:", e)