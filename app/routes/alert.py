from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.alert import AlertResponse
from ..services.auth import AuthService

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

@router.get("/", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    # Implement alert retrieval
    pass