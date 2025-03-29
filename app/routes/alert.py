from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.alert import AlertResponse

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

@router.get("/", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    # Implement alert retrieval
    pass