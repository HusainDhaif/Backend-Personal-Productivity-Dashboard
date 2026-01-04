from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from models.habit import HabitModel
from models.user import UserModel, UserRole
from serializers.habit import HabitCreate, HabitSchema, HabitUpdate, HabitWithDetails, HabitStats
from database import get_db
from dependencies.get_current_user import get_current_user
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.post("/", response_model=HabitSchema, status_code=status.HTTP_201_CREATED)
async def create_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new habit.
    """
    try:
        new_habit = HabitModel(
            user_id=current_user.id,
            title=habit.title,
            description=habit.description,
            is_completed=False,
            completed_at=None
        )
        
        db.add(new_habit)
        db.commit()
        db.refresh(new_habit)
        
        return new_habit
    except Exception as e:
        db.rollback()
        print(f"Error creating habit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create habit: {str(e)}"
        )

@router.get("/my", response_model=List[HabitWithDetails])
async def get_my_habits(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user's habits.
    """
    try:
        query = db.query(HabitModel).options(
            joinedload(HabitModel.user)
        ).filter(HabitModel.user_id == current_user.id)

        if completed is not None:
            query = query.filter(HabitModel.is_completed == completed)
        
        habits = query.order_by(HabitModel.created_at.desc()).all()
        
        return habits
    except Exception as e:
        print(f"Error fetching habits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch habits: {str(e)}"
        )

@router.get("/admin/all", response_model=List[HabitWithDetails])
async def get_all_habits_admin(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all habits - ADMIN ONLY.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view all habits"
        )
    
    query = db.query(HabitModel).options(
        joinedload(HabitModel.user)
    )
    
    # Apply filters
    if user_id:
        query = query.filter(HabitModel.user_id == user_id)
    
    if completed is not None:
        query = query.filter(HabitModel.is_completed == completed)
    
    # Order by creation date (newest first)
    query = query.order_by(HabitModel.created_at.desc())
    
    habits = query.all()
    
    return habits

@router.get("/{habit_id}", response_model=HabitWithDetails)
async def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific habit by ID.
    Users can only see their own habits, admins can see all.
    """
    habit = db.query(HabitModel).options(
        joinedload(HabitModel.user)
    ).filter(HabitModel.id == habit_id).first()
    
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id {habit_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN.value and habit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own habits"
        )
    
    return habit

@router.put("/{habit_id}", response_model=HabitSchema)
async def update_habit(
    habit_id: int,
    habit_update: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a habit (e.g., mark as completed).
    Users can only update their own habits.
    """
    try:
        habit = db.query(HabitModel).filter(HabitModel.id == habit_id).first()
        
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Habit with id {habit_id} not found"
            )
        
        # Check permissions
        if current_user.role != UserRole.ADMIN.value and habit.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own habits"
            )
        
        # Handle completion status
        update_data = habit_update.dict(exclude_unset=True)
        
        # If marking as completed, set completed_at timestamp
        if 'is_completed' in update_data and update_data['is_completed']:
            update_data['completed_at'] = datetime.now(timezone.utc)
        elif 'is_completed' in update_data and not update_data['is_completed']:
            update_data['completed_at'] = None
        
        for key, value in update_data.items():
            setattr(habit, key, value)
        
        db.commit()
        db.refresh(habit)
        return habit
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating habit: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update habit: {str(e)}"
        )

@router.delete("/{habit_id}")
async def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a habit.
    Users can only delete their own habits.
    """
    habit = db.query(HabitModel).filter(HabitModel.id == habit_id).first()
    
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id {habit_id} not found"
        )
    
    # Check permissions
    if current_user.role != UserRole.ADMIN.value and habit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own habits"
        )
    
    try:
        db.delete(habit)
        db.commit()
        
        return {"message": f"Habit {habit_id} has been deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete habit: {str(e)}"
        )

@router.get("/stats/my", response_model=HabitStats)
async def get_habit_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get habit statistics for current user.
    """
    try:
        # Get statistics
        total_habits = db.query(HabitModel).filter(HabitModel.user_id == current_user.id).count()
        completed_habits = db.query(HabitModel).filter(
            HabitModel.user_id == current_user.id,
            HabitModel.is_completed == True
        ).count()
        incomplete_habits = total_habits - completed_habits
        
        return HabitStats(
            total_habits=total_habits,
            completed_habits=completed_habits,
            incomplete_habits=incomplete_habits
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get habit statistics: {str(e)}"
        )
