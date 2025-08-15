from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import require_superadmin


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _: models.User = Depends(require_superadmin)) -> Dict[str, Any]:
    total_users = db.query(models.User).count()
    users_by_role_rows = (
        db.query(models.User.role, func.count(models.User.id)).group_by(models.User.role).all()
    )
    users_by_role = {role or "unknown": count for role, count in users_by_role_rows}

    total_regions = db.query(models.Region).count()
    total_buildings = db.query(models.Building).count()
    total_rooms = db.query(models.Room).count()
    rooms_by_status_rows = (
        db.query(models.Room.status, func.count(models.Room.id))
        .group_by(models.Room.status)
        .all()
    )
    rooms_by_status = {status or "unknown": count for status, count in rooms_by_status_rows}

    total_contracts = db.query(models.Contract).count()
    contracts_by_status_rows = (
        db.query(models.Contract.status, func.count(models.Contract.id))
        .group_by(models.Contract.status)
        .all()
    )
    contracts_by_status = {status or "unknown": count for status, count in contracts_by_status_rows}

    total_approvals = db.query(models.Approval).count()

    return {
        "totals": {
            "users": total_users,
            "regions": total_regions,
            "buildings": total_buildings,
            "rooms": total_rooms,
            "contracts": total_contracts,
            "approvals": total_approvals,
        },
        "users_by_role": users_by_role,
        "rooms_by_status": rooms_by_status,
        "contracts_by_status": contracts_by_status,
    }


@router.get("/regions")
def dashboard_regions(db: Session = Depends(get_db), _: models.User = Depends(require_superadmin)) -> List[Dict[str, Any]]:
    regions = db.query(models.Region).all()
    result: List[Dict[str, Any]] = []
    for region in regions:
        buildings_count = db.query(models.Building).filter(models.Building.region_id == region.id).count()
        rooms_count = (
            db.query(models.Room)
            .join(models.Building, models.Room.building_id == models.Building.id)
            .filter(models.Building.region_id == region.id)
            .count()
        )
        free_rooms = (
            db.query(models.Room)
            .join(models.Building, models.Room.building_id == models.Building.id)
            .filter(models.Building.region_id == region.id, models.Room.status == "free")
            .count()
        )
        booked_rooms = (
            db.query(models.Room)
            .join(models.Building, models.Room.building_id == models.Building.id)
            .filter(models.Building.region_id == region.id, models.Room.status == "booked")
            .count()
        )
        contracts_count = (
            db.query(models.Contract)
            .join(models.Building, models.Contract.building_id == models.Building.id)
            .filter(models.Building.region_id == region.id)
            .count()
        )
        result.append(
            {
                "region_id": region.id,
                "region_name": region.name,
                "buildings_count": buildings_count,
                "rooms_count": rooms_count,
                "free_rooms": free_rooms,
                "booked_rooms": booked_rooms,
                "contracts_count": contracts_count,
            }
        )
    return result


@router.get("/buildings")
def dashboard_buildings(db: Session = Depends(get_db), _: models.User = Depends(require_superadmin)) -> List[Dict[str, Any]]:
    buildings = db.query(models.Building).all()
    result: List[Dict[str, Any]] = []
    for building in buildings:
        rooms_count = db.query(models.Room).filter(models.Room.building_id == building.id).count()
        free_rooms = (
            db.query(models.Room)
            .filter(models.Room.building_id == building.id, models.Room.status == "free")
            .count()
        )
        booked_rooms = (
            db.query(models.Room)
            .filter(models.Room.building_id == building.id, models.Room.status == "booked")
            .count()
        )
        contracts_count = db.query(models.Contract).filter(models.Contract.building_id == building.id).count()
        photos_count = db.query(models.BuildingPhoto).filter(models.BuildingPhoto.building_id == building.id).count()

        result.append(
            {
                "building_id": building.id,
                "building_name": building.name,
                "city": building.city,
                "region_id": building.region_id,
                "rooms_count": rooms_count,
                "free_rooms": free_rooms,
                "booked_rooms": booked_rooms,
                "contracts_count": contracts_count,
                "photos_count": photos_count,
                "price_per_m2": building.price_per_m2,
                "total_area": building.total_area,
            }
        )
    return result


