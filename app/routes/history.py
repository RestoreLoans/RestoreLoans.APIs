from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.history import HistoryResponse
from app.services.auth import AuthService

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/statements", response_model=list[HistoryResponse])
def get_statements(db: Session = Depends(get_db)):
    # Implement statement retrieval
    pass