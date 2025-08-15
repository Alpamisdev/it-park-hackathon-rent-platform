from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/regions", tags=["Regions"])


@router.post("/", response_model=schemas.RegionRead, status_code=status.HTTP_201_CREATED)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db)):
    db_region = models.Region(**region.model_dump())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


@router.get("/", response_model=List[schemas.RegionRead])
def list_regions(db: Session = Depends(get_db)):
    return db.query(models.Region).all()


@router.get("/{region_id}", response_model=schemas.RegionRead)
def get_region(region_id: int, db: Session = Depends(get_db)):
    db_region = db.get(models.Region, region_id)
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    return db_region


@router.put("/{region_id}", response_model=schemas.RegionRead)
def update_region(region_id: int, region_update: schemas.RegionUpdate, db: Session = Depends(get_db)):
    db_region = db.get(models.Region, region_id)
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    for key, value in region_update.model_dump(exclude_unset=True).items():
        setattr(db_region, key, value)
    db.commit()
    db.refresh(db_region)
    return db_region


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(region_id: int, db: Session = Depends(get_db)):
    db_region = db.get(models.Region, region_id)
    if not db_region:
        raise HTTPException(status_code=404, detail="Region not found")
    db.delete(db_region)
    db.commit()
    return None


