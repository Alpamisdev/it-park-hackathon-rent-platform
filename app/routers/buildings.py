from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/buildings", tags=["Buildings"])


@router.post("/", response_model=schemas.BuildingRead, status_code=status.HTTP_201_CREATED)
def create_building(building: schemas.BuildingCreate, db: Session = Depends(get_db)):
    db_building = models.Building(**building.model_dump())
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building


@router.get("/", response_model=List[schemas.BuildingRead])
def list_buildings(db: Session = Depends(get_db)):
    return db.query(models.Building).all()


@router.get("/{building_id}", response_model=schemas.BuildingRead)
def get_building(building_id: int, db: Session = Depends(get_db)):
    db_building = db.get(models.Building, building_id)
    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building


@router.put("/{building_id}", response_model=schemas.BuildingRead)
def update_building(building_id: int, building_update: schemas.BuildingUpdate, db: Session = Depends(get_db)):
    db_building = db.get(models.Building, building_id)
    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")
    for key, value in building_update.model_dump(exclude_unset=True).items():
        setattr(db_building, key, value)
    db.commit()
    db.refresh(db_building)
    return db_building


@router.delete("/{building_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_building(building_id: int, db: Session = Depends(get_db)):
    db_building = db.get(models.Building, building_id)
    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")
    db.delete(db_building)
    db.commit()
    return None


