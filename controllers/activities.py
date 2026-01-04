from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_activities():
    return {"message": "Activities endpoint placeholder"}
