# from fastapi import FastAPI
# from controllers.users import router as UsersRouter
# from controllers.daily_goals import router as DailyGoalsRouter
# from controllers.tasks import router as TasksRouter
# from controllers.habits import router as HabitsRouter
# from controllers.notes import router as NotesRouter
# from fastapi.middleware.cors import CORSMiddleware
# import os

# frontendUrl = os.getenv("FRONTENDURL")

# app = FastAPI(
#     title="Personal Productivity Dashboard API",
#     description="A personal productivity dashboard API built with FastAPI",
#     version="1.0.0"
# )

# # CORS Configuration
# origins = [
#     "http://127.0.0.1:5173",
#     "http://localhost:5173"
# ]

# # Add production frontend URL if exists
# if frontendUrl:
#     origins.append(frontendUrl)
   

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,  # Specific origins
#     allow_origin_regex=r"https://.*-frontend-.*\.vercel\.app",  # Regex for Vercel previews
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
#     allow_headers=["*"],
#     expose_headers=["*"]
# )

# app.include_router(UsersRouter, prefix="/api", tags=["Users"])
# app.include_router(DailyGoalsRouter, prefix="/api", tags=["Daily Goals"])
# app.include_router(TasksRouter, prefix="/api/tasks", tags=["Tasks"]) 
# app.include_router(NotesRouter, prefix="/api", tags=["Notes"])
# app.include_router(HabitsRouter, prefix="/api/habits", tags=["Habits"])

# @app.get('/')
# def home():
#     return {'message': 'Welcome to Personal Productivity Dashboard API! Visit /docs for API documentation.'}

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from controllers.users import router as UsersRouter
from controllers.tasks import router as TasksRouter
from controllers.notes import router as NotesRouter
from controllers.habits import router as HabitsRouter
from controllers.daily_goals import router as DailyGoalsRouter
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Personal Productivity Dashboard API",
    description="A personal productivity dashboard API built with FastAPI",
    version="1.0.0"
)

# CORS configuration - Allow requests from frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and return meaningful error messages"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    error_detail = str(exc)
    if isinstance(exc, SQLAlchemyError):
        error_detail = "Database error occurred. Please check the logs."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": error_detail,
            "path": str(request.url)
        }
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )

# Include all routers with correct prefixes to match frontend URLs
app.include_router(UsersRouter, prefix="/api", tags=["Users"])
app.include_router(TasksRouter, prefix="/api/tasks", tags=["Tasks"])
app.include_router(NotesRouter, prefix="/api", tags=["Notes"])
app.include_router(HabitsRouter, prefix="/api/habits", tags=["Habits"])
app.include_router(DailyGoalsRouter, prefix="/api", tags=["Daily Goals"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        from models.base import Base
        from database import engine
        from sqlalchemy import inspect, text
        
        logger.info("Checking database connection...")
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        
        logger.info("Database connection successful")
        
        # Create tables if they don't exist
        logger.info("Creating/verifying database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ All tables verified")
        
        # Check for role column in users table
        inspector = inspect(engine)
        if 'users' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('users')]
            if 'role' not in columns:
                logger.warning("'role' column missing in users table. Run: python init_database.py")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    return {"message": "Backend is running. Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
