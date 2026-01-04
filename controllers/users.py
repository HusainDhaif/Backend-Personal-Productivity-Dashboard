from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, ProgrammingError
from sqlalchemy import text
from models.user import UserModel, UserRole  
from serializers.user import UserSchema, UserResponseSchema, UserLogin, UserToken
from database import get_db

router = APIRouter()

@router.post("/register")
def create_user(user: UserSchema, db: Session = Depends(get_db)):
    """
    Register a new user.
    Returns JSON with success message and user data, or error message.
    """
    try:
        # Check if the username or email already exists
        # Use raw SQL to avoid column errors if role column doesn't exist yet
        try:
            existing_user = db.query(UserModel).filter(
                (UserModel.username == user.username) | (UserModel.email == user.email)
            ).first()
        except ProgrammingError as pe:
            # If role column doesn't exist, query without it
            db.rollback()
            error_msg = str(pe.orig) if hasattr(pe, 'orig') else str(pe)
            print(f"Database schema error (role column missing): {error_msg}")
            return {
                "error": "Database schema error",
                "message": "The 'role' column is missing from the users table. Please run the migration script: python fix_role_column.py",
                "backend_error": error_msg,
                "fix_instruction": "Run: python fix_role_column.py"
            }

        if existing_user:
            if existing_user.username == user.username:
                return {
                    "error": "Username already exists",
                    "message": "A user with this username already exists. Please choose a different username."
                }
            else:
                return {
                    "error": "Email already exists",
                    "message": "A user with this email already exists. Please use a different email."
                }

        # Set default role if not provided - handle both string and enum
        if user.role:
            if isinstance(user.role, str):
                user_role = user.role.upper()  # Convert to uppercase string
            else:
                user_role = user.role.value if hasattr(user.role, 'value') else str(user.role).upper()
        else:
            user_role = UserRole.CUSTOMER.value
        
        # Create new user
        new_user = UserModel(
            username=user.username, 
            email=user.email,
            role=user_role  # Store as string 'CUSTOMER' or 'ADMIN'
        )
        
        # Use the set_password method to hash the password
        new_user.set_password(user.password)

        # Add user to database with proper transaction handling
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate token for immediate login
        try:
            token = new_user.generate_token()
        except Exception as token_err:
            print(f"Token generation error (non-critical): {str(token_err)}")
            token = None

        # Return success response with user data
        response_data = {
            "message": "User created successfully",
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role or "CUSTOMER"
        }
        
        # Add token if generated
        if token:
            response_data["token"] = token

        return response_data
        
    except ProgrammingError as e:
        # Handle database schema errors (missing columns, etc.)
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        error_type = type(e).__name__
        print(f"Programming error during registration: {error_type} - {error_msg}")
        
        if "role" in error_msg.lower() or "column" in error_msg.lower():
            return {
                "error": "Database schema error",
                "message": "The 'role' column is missing from the users table. Please run the migration script.",
                "backend_error": error_msg,
                "error_type": error_type,
                "fix_instruction": "Run: python fix_role_column.py"
            }
        else:
            return {
                "error": "Database schema error",
                "message": f"Database schema issue detected: {error_msg}",
                "backend_error": error_msg,
                "error_type": error_type
            }
        
    except IntegrityError as e:
        # Handle database integrity errors (unique constraints, etc.)
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        error_type = type(e).__name__
        print(f"Integrity error during registration: {error_type} - {error_msg}")
        
        if "username" in error_msg.lower():
            return {
                "error": "Username already exists",
                "message": "A user with this username already exists.",
                "backend_error": error_msg
            }
        elif "email" in error_msg.lower():
            return {
                "error": "Email already exists",
                "message": "A user with this email already exists.",
                "backend_error": error_msg
            }
        else:
            return {
                "error": "Database constraint error",
                "message": "Registration failed due to a database constraint violation.",
                "backend_error": error_msg,
                "error_type": error_type
            }
            
    except SQLAlchemyError as e:
        # Handle other SQLAlchemy errors
        db.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"SQLAlchemy error during registration: {error_type} - {error_msg}")
        return {
            "error": "Database error",
            "message": "Registration failed due to a database error. Please try again later.",
            "backend_error": error_msg,
            "error_type": error_type
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
        
    except Exception as e:
        # Handle any other unexpected errors
        db.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"Unexpected error during registration: {error_type} - {error_msg}")
        return {
            "error": "Registration failed",
            "message": f"An unexpected error occurred: {error_msg}",
            "backend_error": error_msg,
            "error_type": error_type
        }


@router.post("/login", response_model=UserToken)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Login endpoint - authenticates user and returns JWT token.
    """
    try:
        # Find the user by username
        db_user = db.query(UserModel).filter(UserModel.username == user.username).first()

        # Check if the user exists and if the password is correct
        if not db_user or not db_user.verify_password(user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid username or password"
            )

        # Generate JWT token
        token = db_user.generate_token()
        
        # Get role, defaulting to CUSTOMER if role is None
        user_role = db_user.role if db_user.role else UserRole.CUSTOMER.value

        return {
            "token": token, 
            "message": "Login successful",
            "role": user_role
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to an internal error"
        )
