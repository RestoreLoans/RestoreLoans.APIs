from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.history import HistoryResponse
from app.services.auth import AuthService
# from app.models.history import History  # Assuming History is the SQLAlchemy model for historical statements


router = APIRouter(
    prefix="/history",
    tags=["History"]
)

@router.get("/statements", response_model=list[HistoryResponse])
def get_statements(db: Session = Depends(get_db)):
    # Query all historical statements from the database
    statements = db.query(History).all()

    # Return the list of statements
    return statements