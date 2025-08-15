from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/building-photos", tags=["Building Photos"])


@router.post("/", response_model=schemas.BuildingPhotoRead, status_code=status.HTTP_201_CREATED)
def create_building_photo(photo: schemas.BuildingPhotoCreate, db: Session = Depends(get_db)):
    db_photo = models.BuildingPhoto(**photo.model_dump())
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo


@router.get("/", response_model=List[schemas.BuildingPhotoRead])
def list_building_photos(db: Session = Depends(get_db)):
    return db.query(models.BuildingPhoto).all()


@router.get("/{photo_id}", response_model=schemas.BuildingPhotoRead)
def get_building_photo(photo_id: int, db: Session = Depends(get_db)):
    db_photo = db.get(models.BuildingPhoto, photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Building photo not found")
    return db_photo


@router.put("/{photo_id}", response_model=schemas.BuildingPhotoRead)
def update_building_photo(photo_id: int, photo_update: schemas.BuildingPhotoUpdate, db: Session = Depends(get_db)):
    db_photo = db.get(models.BuildingPhoto, photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Building photo not found")
    for key, value in photo_update.model_dump(exclude_unset=True).items():
        setattr(db_photo, key, value)
    db.commit()
    db.refresh(db_photo)
    return db_photo


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_building_photo(photo_id: int, db: Session = Depends(get_db)):
    db_photo = db.get(models.BuildingPhoto, photo_id)
    if not db_photo:
        raise HTTPException(status_code=404, detail="Building photo not found")
    db.delete(db_photo)
    db.commit()
    return None


