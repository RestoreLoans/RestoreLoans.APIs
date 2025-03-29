from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transaction import TransactionResponse
from app.services.auth import AuthService

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    # Implement transaction retrieval
    pass