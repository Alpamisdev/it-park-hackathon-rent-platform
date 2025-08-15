from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/amenities", tags=["Amenities"])


@router.post("/", response_model=schemas.AmenityRead, status_code=status.HTTP_201_CREATED)
def create_amenity(amenity: schemas.AmenityCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Amenity).filter(models.Amenity.name == amenity.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Amenity already exists")
    a = models.Amenity(**amenity.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("/", response_model=List[schemas.AmenityRead])
def list_amenities(active: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Amenity)
    if active is not None:
        q = q.filter(models.Amenity.is_active == active)
    return q.all()


@router.put("/{amenity_id}", response_model=schemas.AmenityRead)
def update_amenity(amenity_id: int, amenity: schemas.AmenityCreate, db: Session = Depends(get_db)):
    a = db.get(models.Amenity, amenity_id)
    if not a:
        raise HTTPException(status_code=404, detail="Amenity not found")
    # Unique name, case-insensitive
    existing = (
        db.query(models.Amenity)
        .filter(models.Amenity.id != amenity_id)
        .filter(models.Amenity.name.ilike(amenity.name))
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Amenity with this name already exists")
    a.name = amenity.name
    a.icon = amenity.icon
    a.is_active = amenity.is_active
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{amenity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_amenity(amenity_id: int, db: Session = Depends(get_db)):
    a = db.get(models.Amenity, amenity_id)
    if not a:
        raise HTTPException(status_code=404, detail="Amenity not found")
    # Soft delete: deactivate
    a.is_active = False
    db.add(a)
    db.commit()
    return None


