from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
from models.daily_goal import DailyGoalModel
from models.user import UserModel, UserRole
from serializers.daily_goal import DailyGoalCreate, DailyGoalUpdate, DailyGoalSchema
from database import get_db
from dependencies.get_current_user import get_current_user

router = APIRouter()

# GET all daily goals for current user
@router.get('/daily-goals', response_model=List[DailyGoalSchema])
def get_daily_goals(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    goal_date: Optional[date] = Query(None, description="Filter by goal date"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(20, ge=1, le=100, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get all daily goals for the current user with optional filtering and search.
    
    - **goal_date**: Filter by specific date
    - **completed**: Filter by completion status
    - **search**: Search term in title and description
    - **limit**: Number of results per page (1-100)
    - **offset**: Pagination offset
    
    Returns daily goals ordered by newest first.
    """
    try:
        query = db.query(DailyGoalModel).filter(
            DailyGoalModel.user_id == current_user.id
        ).options(joinedload(DailyGoalModel.user))
        
        # Apply filters
        if goal_date:
            query = query.filter(DailyGoalModel.goal_date == goal_date)
        if completed is not None:
            query = query.filter(DailyGoalModel.is_completed == completed)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (DailyGoalModel.title.ilike(search_term)) | 
                (DailyGoalModel.description.ilike(search_term))
            )
        
        # Order by creation date (newest first) and apply pagination
        goals = query.order_by(DailyGoalModel.created_at.desc())\
                     .limit(limit)\
                     .offset(offset)\
                     .all()
        
        return goals
    except Exception as e:
        print(f"Error fetching daily goals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch daily goals: {str(e)}"
        )

# GET single daily goal
@router.get('/daily-goals/{goal_id}', response_model=DailyGoalSchema)
def get_daily_goal(
    goal_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single daily goal by ID.
    
    Returns daily goal details with user information.
    """
    goal = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).options(joinedload(DailyGoalModel.user)).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Daily goal with id {goal_id} not found"
        )
    
    # Check if user owns this goal
    if goal.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own daily goals"
        )
    
    return goal

# POST create daily goal (requires authentication)
@router.post('/daily-goals', response_model=DailyGoalSchema, status_code=status.HTTP_201_CREATED)
def create_daily_goal(
    goal: DailyGoalCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new daily goal.
    
    - **title**: Goal title (1-100 characters)
    - **description**: Goal description
    - **goal_date**: Date for the daily goal
    
    Requires authentication. The authenticated user becomes the goal owner.
    By default, new goals are created as not completed.
    """
    try:
        new_goal = DailyGoalModel(
            title=goal.title,
            description=goal.description,
            goal_date=goal.goal_date,
            is_completed=False,  # New goals are not completed by default
            user_id=current_user.id  # Authenticated user is the owner
        )
        
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        
        return new_goal
    except Exception as e:
        db.rollback()
        print(f"Error creating daily goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create daily goal: {str(e)}"
        )

# PUT update daily goal (requires authentication - owner OR admin)
@router.put('/daily-goals/{goal_id}', response_model=DailyGoalSchema)
def update_daily_goal(
    goal_id: int,
    goal_update: DailyGoalUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a daily goal.
    
    Only the goal owner or an admin can update a goal.
    All fields are optional - only provided fields will be updated.
    Use is_completed field to mark goal as completed.
    """
    try:
        db_goal = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).first()
        
        if not db_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily goal with id {goal_id} not found"
            )
        
        # Authorization: goal owner OR admin can update
        if db_goal.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this daily goal"
            )
        
        # Update only provided fields
        update_data = goal_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_goal, key, value)
        
        db.commit()
        db.refresh(db_goal)
        return db_goal
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating daily goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update daily goal: {str(e)}"
        )

# DELETE daily goal
@router.delete('/daily-goals/{goal_id}')
def delete_daily_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    DELETE a daily goal permanently (hard delete).
    
    Only the goal owner or an admin can delete a goal.
    This performs a HARD DELETE - goal is removed from database entirely.
    """
    try:
        db_goal = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).first()
        
        if not db_goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Daily goal with id {goal_id} not found"
            )
        
        # Authorization: goal owner OR admin can delete
        if db_goal.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this daily goal"
            )
        
        db.delete(db_goal)
        db.commit()
        
        return {"message": f"Daily goal with id {goal_id} has been permanently deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting daily goal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete daily goal: {str(e)}"
        )

# GET daily goals by user
@router.get('/users/{user_id}/daily-goals', response_model=List[DailyGoalSchema])
def get_user_daily_goals(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all daily goals by a specific user.
    
    Users can only view their own goals unless they are admin.
    """
    # Check if user is accessing their own goals or is admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these daily goals"
        )
    
    goals = db.query(DailyGoalModel).filter(
        DailyGoalModel.user_id == user_id
    ).options(joinedload(DailyGoalModel.user)).order_by(DailyGoalModel.created_at.desc())\
     .limit(limit)\
     .offset(offset)\
     .all()
    
    return goals

# GET all daily goals (admin only)
@router.get('/admin/daily-goals', response_model=List[DailyGoalSchema])
def get_all_daily_goals_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    show_completed: bool = Query(True, description="Include completed goals"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all daily goals - Admin only.
    
    Only users with ADMIN role can access this endpoint.
    """
    # Authorization: only admin can access
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    query = db.query(DailyGoalModel).options(joinedload(DailyGoalModel.user))
    
    # Filter out completed goals unless explicitly requested
    if not show_completed:
        query = query.filter(DailyGoalModel.is_completed == False)
    
    goals = query.order_by(DailyGoalModel.created_at.desc())\
                 .limit(limit)\
                 .offset(offset)\
                 .all()
    
    return goals
