from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.userRoles import userRole
from app.schemas.userRoles import UserRoleCreate, UserRoleResponse

router = APIRouter(
    prefix="/user-roles",
    tags=["User Roles"]
)

@router.post("/", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def create_user_role(role_data: UserRoleCreate, db: Session = Depends(get_db)):
    # Check if the role already exists
    existing_role = db.query(userRole).filter(userRole.role_name == role_data.role_name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.role_name}' already exists."
        )

    # Create a new role
    new_role = userRole(
        role_name=role_data.role_name,
        description=role_data.description,
        status=role_data.status
    )

    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return new_role

@router.get("/", response_model=list[UserRoleResponse], status_code=status.HTTP_200_OK)
def get_all_user_roles(db: Session = Depends(get_db)):
    # Retrieve all roles
    roles = db.query(userRole).all()
    return roles

@router.get("/{role_id}", response_model=UserRoleResponse, status_code=status.HTTP_200_OK)
def get_user_role(role_id: int, db: Session = Depends(get_db)):
    # Retrieve a role by ID
    role = db.query(userRole).filter(userRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found."
        )
    return role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_role(role_id: int, db: Session = Depends(get_db)):
    # Delete a role by ID
    role = db.query(userRole).filter(userRole.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found."
        )

    db.delete(role)
    db.commit()
    return