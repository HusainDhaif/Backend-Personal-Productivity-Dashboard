from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from models.note import NoteModel
from models.user import UserModel, UserRole
from serializers.note import NoteCreate, NoteUpdate, NoteSchema
from database import get_db
from dependencies.get_current_user import get_current_user

router = APIRouter()

@router.post('/notes', response_model=NoteSchema, status_code=status.HTTP_201_CREATED)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new note.
    """
    try:
        new_note = NoteModel(
            user_id=current_user.id,
            title=note.title,
            content=note.content
        )
        
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        
        return new_note
    except Exception as e:
        db.rollback()
        print(f"Error creating note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get('/notes', response_model=List[NoteSchema])
def get_user_notes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search in title and content")
):
    """
    Get all notes for the current user.
    """
    try:
        query = db.query(NoteModel).filter(
            NoteModel.user_id == current_user.id
        ).options(joinedload(NoteModel.user))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (NoteModel.title.ilike(search_term)) | 
                (NoteModel.content.ilike(search_term))
            )
        
        notes = query.order_by(NoteModel.created_at.desc()).all()
        
        return notes
    except Exception as e:
        print(f"Error fetching notes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notes: {str(e)}"
        )


@router.get('/notes/{note_id}', response_model=NoteSchema)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get a single note by ID.
    """
    note = db.query(NoteModel).filter(NoteModel.id == note_id).options(joinedload(NoteModel.user)).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id {note_id} not found"
        )
    
    # Check if user owns this note
    if note.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own notes"
        )
    
    return note


@router.put('/notes/{note_id}', response_model=NoteSchema)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a note.
    Users can only update their own notes.
    """
    try:
        note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        # Check permissions
        if note.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own notes"
            )
        
        update_data = note_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(note, key, value)
        
        db.commit()
        db.refresh(note)
        
        return note
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update note: {str(e)}"
        )


@router.delete('/notes/{note_id}')
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a note.
    Users can only delete their own notes.
    """
    try:
        note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
        
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with id {note_id} not found"
            )
        
        # Check permissions
        if note.user_id != current_user.id and current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own notes"
            )
        
        db.delete(note)
        db.commit()
        
        return {"message": f"Note {note_id} has been deleted successfully", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete note: {str(e)}"
        )
