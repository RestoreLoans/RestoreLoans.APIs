from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.alert import AlertResponse
from app.models.alert import Alert  # Assuming Alert is the SQLAlchemy model for alerts
from fastapi import HTTPException, status
from app.services.auth import AuthService

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

@router.get("/", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    # Query all alerts from the database
    alerts = db.query(Alert).all()

    # Return the list of alerts
    return alerts