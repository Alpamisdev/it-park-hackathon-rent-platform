from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/signers", tags=["Signers"])


@router.get("/", response_model=List[schemas.SignerRead])
def list_signers(
    region_id: Optional[int] = Query(None),
    position: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Signer)
    if region_id is not None:
        q = q.filter(models.Signer.region_id == region_id)
    if position:
        q = q.filter(models.Signer.position == position)
    return q.order_by(models.Signer.signing_order.asc()).all()


@router.post("/", response_model=schemas.SignerRead, status_code=status.HTTP_201_CREATED)
def create_signer(signer: schemas.SignerCreate, db: Session = Depends(get_db)):
    # Ensure unique signing_order per region if provided
    if signer.region_id is not None:
        exists = (
            db.query(models.Signer)
            .filter(models.Signer.region_id == signer.region_id)
            .filter(models.Signer.signing_order == signer.signing_order)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Signing order already used for this region")
    s = models.Signer(**signer.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/{signer_id}", response_model=schemas.SignerRead)
def update_signer(signer_id: int, payload: schemas.SignerUpdate, db: Session = Depends(get_db)):
    s = db.get(models.Signer, signer_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signer not found")
    data = payload.model_dump(exclude_unset=True)
    if "signing_order" in data and s.region_id is not None:
        exists = (
            db.query(models.Signer)
            .filter(models.Signer.region_id == (data.get("region_id") or s.region_id))
            .filter(models.Signer.signing_order == data["signing_order"], models.Signer.id != signer_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Signing order already used for this region")
    for k, v in data.items():
        setattr(s, k, v)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{signer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signer(signer_id: int, db: Session = Depends(get_db)):
    s = db.get(models.Signer, signer_id)
    if not s:
        raise HTTPException(status_code=404, detail="Signer not found")
    db.delete(s)
    db.commit()
    return None


