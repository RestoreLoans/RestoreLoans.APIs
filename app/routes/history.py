from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.history import StatementHistory
from app.schemas.history import StatementHistoryCreate, StatementHistoryResponse

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.post("/", response_model=StatementHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_statement_history(history_data: StatementHistoryCreate, db: Session = Depends(get_db)):
    # Create a new statement history instance
    new_history = StatementHistory(
        user_id=history_data.user_id,
        loan_id=history_data.loan_id,
        statement_type=history_data.statement_type,
        file_path=history_data.file_path
    )

    # Add the statement history to the database
    db.add(new_history)
    db.commit()
    db.refresh(new_history)  # Refresh to get the updated data from the database

    return new_history

@router.get("/", response_model=list[StatementHistoryResponse], status_code=status.HTTP_200_OK)
def get_statement_history(db: Session = Depends(get_db)):
    # Retrieve all statement history records
    history_records = db.query(StatementHistory).all()
    return history_records