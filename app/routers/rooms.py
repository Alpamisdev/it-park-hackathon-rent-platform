from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/", response_model=schemas.RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: Session = Depends(get_db)):
    db_room = models.Room(**room.model_dump())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.get("/", response_model=List[schemas.RoomRead])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(models.Room).all()


@router.get("/{room_id}", response_model=schemas.RoomRead)
def get_room(room_id: int, db: Session = Depends(get_db)):
    db_room = db.get(models.Room, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room


@router.put("/{room_id}", response_model=schemas.RoomRead)
def update_room(room_id: int, room_update: schemas.RoomUpdate, db: Session = Depends(get_db)):
    db_room = db.get(models.Room, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    for key, value in room_update.model_dump(exclude_unset=True).items():
        setattr(db_room, key, value)
    db.commit()
    db.refresh(db_room)
    return db_room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    db_room = db.get(models.Room, room_id)
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    db.delete(db_room)
    db.commit()
    return None


