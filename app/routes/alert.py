from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.alert import AlertResponse, AlertCreate, AlertUpdate
from app.models.alert import Alert  # Assuming Alert is the SQLAlchemy model for alerts

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

# Create an alert
@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    new_alert = Alert(**alert.dict())
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

# Read all alerts
@router.get("/", response_model=list[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return alerts

# Read a single alert by ID
@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert

# Update an alert
@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, alert_data: AlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    for key, value in alert_data.dict(exclude_unset=True).items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    return alert

# Delete an alert
@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return
# In app/routes/alert.py
@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    # Use model_dump() for Pydantic v2+
    new_alert = Alert(**alert.model_dump(exclude_unset=True))
    db.add(new_alert)
    try:
        db.commit()
        db.refresh(new_alert)
    except Exception as e:
        db.rollback()
        # Consider logging the error e
        raise HTTPException(status_code=500, detail="Failed to create alert.")
    return new_alert

# Also update the update route to use model_dump()
@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, alert_data: AlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    # Use model_dump() for Pydantic v2+
    for key, value in alert_data.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    try:
        db.commit()
        db.refresh(alert)
    except Exception as e:
        db.rollback()
        # Consider logging the error e
        raise HTTPException(status_code=500, detail="Failed to update alert.")
    return alert
