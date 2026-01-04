from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models.task import TaskModel
from models.user import UserModel, UserRole
from serializers.task import TaskCreate, TaskUpdate, TaskSchema
from database import get_db
from dependencies.get_current_user import get_current_user
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.post("/", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new task.
    """
    try:
        new_task = TaskModel(
            title=task.title,
            description=task.description,
            due_date=task.due_date,
            user_id=current_user.id,
            is_completed=False
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except Exception as e:
        db.rollback()
        print(f"Error creating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/", response_model=List[TaskSchema])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search in title or description")
):
    """
    Get all tasks for the current user.
    """
    try:
        query = db.query(TaskModel).options(joinedload(TaskModel.user)).filter(
            TaskModel.user_id == current_user.id
        )

        if completed is not None:
            query = query.filter(TaskModel.is_completed == completed)
        
        if search:
            query = query.filter(
                (TaskModel.title.ilike(f'%{search}%')) |
                (TaskModel.description.ilike(f'%{search}%'))
            )
        
        query = query.order_by(TaskModel.created_at.desc())
        tasks = query.all()
        return tasks
    except Exception as e:
        print(f"Error fetching tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks: {str(e)}"
        )

@router.get("/{task_id}", response_model=TaskSchema)
def get_single_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single task by ID.
    """
    task = db.query(TaskModel).\
        filter(TaskModel.id == task_id).\
        options(joinedload(TaskModel.user)).\
        first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    
    # Check if user owns this task
    if task.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own tasks"
        )
    
    return task

@router.put("/{task_id}", response_model=TaskSchema)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a task.
    """
    try:
        db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        # Check if user owns this task
        if db_task.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own tasks"
            )
        
        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        
        db.commit()
        db.refresh(db_task)
        return db_task
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Permanently delete a task.
    """
    try:
        db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {task_id} not found"
            )
        
        # Check if user owns this task
        if db_task.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own tasks"
            )
        
        # Permanently delete from database
        db.delete(db_task)
        db.commit()
        
        return {"message": f"Task with id {task_id} has been permanently deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.get("/admin/all", response_model=List[TaskSchema])
def get_all_tasks_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all tasks for admin dashboard 
    ADMIN ONLY.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can view all tasks"
        )
    
    tasks = db.query(TaskModel).\
        options(joinedload(TaskModel.user)).\
        order_by(TaskModel.created_at.desc()).\
        all()
    
    return tasks
