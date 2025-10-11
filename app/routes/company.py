from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.company import Company  # Ensure this matches the provided Company model
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyResponse,
)  # Ensure these schemas match the Company model fields

router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)

@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    company_data = company.model_dump()
    company_data.pop("user_id", None)
    new_company = Company(**company_data)
    db.add(new_company)
    try:
        db.commit()
        db.refresh(new_company)

        user = db.query(User).filter(User.id == company.user_id).first()
        if user:
            user.company_id = new_company.id
            db.commit()
            db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A company with this name or email already exists.",
        )
    return new_company

@router.get("/by-user/{user_id}", response_model=list[CompanyResponse])
def get_companies_by_user(user_id: int, db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.user_id == user_id).all()
    if not companies:
        raise HTTPException(status_code=404, detail="No companies found for this user")
    return companies

@router.get("/", response_model=list[CompanyResponse])
def read_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    companies = db.query(Company).offset(skip).limit(limit).all()
    return companies

@router.get("/{company_id}", response_model=CompanyResponse)
def read_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
)
def update_company(
    company_id: int,
    company_update: CompanyCreate,
    db: Session = Depends(get_db),
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in company_update.model_dump().items():
        if hasattr(company, key):
            setattr(company, key, value)
    try:
        db.commit()
        db.refresh(company)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A company with this email or name already exists.",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company."
        )
    return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return None
