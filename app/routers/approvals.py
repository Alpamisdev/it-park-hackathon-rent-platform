from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.post("/", response_model=schemas.ApprovalRead, status_code=status.HTTP_201_CREATED)
def create_approval(approval: schemas.ApprovalCreate, db: Session = Depends(get_db)):
    db_approval = models.Approval(**approval.model_dump())
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    return db_approval


@router.get("/", response_model=List[schemas.ApprovalRead])
def list_approvals(db: Session = Depends(get_db)):
    return db.query(models.Approval).all()


@router.get("/{approval_id}", response_model=schemas.ApprovalRead)
def get_approval(approval_id: int, db: Session = Depends(get_db)):
    db_approval = db.get(models.Approval, approval_id)
    if not db_approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return db_approval


@router.put("/{approval_id}", response_model=schemas.ApprovalRead)
def update_approval(approval_id: int, approval_update: schemas.ApprovalUpdate, db: Session = Depends(get_db)):
    db_approval = db.get(models.Approval, approval_id)
    if not db_approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    for key, value in approval_update.model_dump(exclude_unset=True).items():
        setattr(db_approval, key, value)
    db.commit()
    db.refresh(db_approval)
    return db_approval


@router.delete("/{approval_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approval(approval_id: int, db: Session = Depends(get_db)):
    db_approval = db.get(models.Approval, approval_id)
    if not db_approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    db.delete(db_approval)
    db.commit()
    return None


