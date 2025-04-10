from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transaction import TransactionResponse
from app.services.auth import AuthService
from app.models.transaction import Transaction  # Assuming Transaction is the SQLAlchemy model for transactions
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    # Query all transactions from the database
    transactions = db.query(Transaction).all()

    # Return the list of transactions
    return transactions