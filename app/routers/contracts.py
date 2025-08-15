from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("/", response_model=schemas.ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(contract: schemas.ContractCreate, db: Session = Depends(get_db)):
    db_contract = models.Contract(**contract.model_dump())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.get("/", response_model=List[schemas.ContractRead])
def list_contracts(db: Session = Depends(get_db)):
    return db.query(models.Contract).all()


@router.get("/{contract_id}", response_model=schemas.ContractRead)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    db_contract = db.get(models.Contract, contract_id)
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return db_contract


@router.put("/{contract_id}", response_model=schemas.ContractRead)
def update_contract(contract_id: int, contract_update: schemas.ContractUpdate, db: Session = Depends(get_db)):
    db_contract = db.get(models.Contract, contract_id)
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    for key, value in contract_update.model_dump(exclude_unset=True).items():
        setattr(db_contract, key, value)
    db.commit()
    db.refresh(db_contract)
    return db_contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    db_contract = db.get(models.Contract, contract_id)
    if not db_contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(db_contract)
    db.commit()
    return None


