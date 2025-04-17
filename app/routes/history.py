from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.history import StatementHistory
from app.models.loan import Loan
from app.schemas.history import StatementHistoryCreate, StatementHistoryResponse, StatementHistoryUpdate

router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.post("/", response_model=StatementHistoryResponse, status_code=status.HTTP_201_CREATED)
def create_statement_history(history_data: StatementHistoryCreate, db: Session = Depends(get_db)):
    # Check if the loan_id exists in the loans table
    loan_exists = db.query(Loan).filter_by(id=history_data.loan_id).first()
    if not loan_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Loan with id {history_data.loan_id} does not exist."
        )

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

@router.get("/{history_id}", response_model=StatementHistoryResponse, status_code=status.HTTP_200_OK)
def get_statement_history_by_id(history_id: int, db: Session = Depends(get_db)):
    # Retrieve a specific statement history record by ID
    history_record = db.query(StatementHistory).filter_by(id=history_id).first()
    if not history_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement history with id {history_id} not found."
        )
    return history_record

@router.put("/{history_id}", response_model=StatementHistoryResponse, status_code=status.HTTP_200_OK)
def update_statement_history(history_id: int, history_data: StatementHistoryUpdate, db: Session = Depends(get_db)):
    # Retrieve the statement history record to update
    history_record = db.query(StatementHistory).filter_by(id=history_id).first()
    if not history_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement history with id {history_id} not found."
        )

    # Update the fields
    for key, value in history_data.dict(exclude_unset=True).items():
        setattr(history_record, key, value)

    db.commit()
    db.refresh(history_record)  # Refresh to get the updated data from the database

    return history_record

@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_statement_history(history_id: int, db: Session = Depends(get_db)):
    # Retrieve the statement history record to delete
    history_record = db.query(StatementHistory).filter_by(id=history_id).first()
    if not history_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Statement history with id {history_id} not found."
        )

    db.delete(history_record)
    db.commit()
    return None