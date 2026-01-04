import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - use environment variable or default to provided connection string
db_URI = os.getenv('DATABASE_URL') or 'postgresql://husaindhaif:H.Dhaif2002@localhost:5432/ppd'
secret = os.getenv('JWT_SECRET') or 'your-secret-key-change-in-production'