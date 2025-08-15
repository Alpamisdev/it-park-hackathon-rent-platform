from fastapi import FastAPI, Depends, Request, HTTPException, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.routers import buildings, contracts, users
from app.routers import regions, rooms, building_photos, approvals, dashboard, amenities
from app.routers import signers
from app.database import Base, engine, get_db, ensure_sqlite_schema
from sqlalchemy.orm import Session
from app import models
from datetime import datetime
from typing import List as _List
import os
import shutil
import time
from app.auth import router as auth_router, require_superadmin, get_current_user

# create database tables and ensure minimal schema updates
Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

app = FastAPI(title="Rent Platform MVP")

# static and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

# routers
app.include_router(buildings.router)
app.include_router(contracts.router)
app.include_router(users.router)
app.include_router(regions.router)
app.include_router(rooms.router)
app.include_router(building_photos.router)
app.include_router(approvals.router)
app.include_router(dashboard.router)
app.include_router(auth_router)
app.include_router(amenities.router)
app.include_router(signers.router)


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    region: str | None = None,
    city: str | None = None,
    max_price: str | None = None,
    db: Session = Depends(get_db),
):
    regions_list = db.query(models.Region).all()

    query = db.query(models.Building)
    # Parse and apply region filter
    if region not in (None, ""):
        try:
            region_id = int(region)
            query = query.filter(models.Building.region_id == region_id)
        except ValueError:
            pass
    if city:
        query = query.filter(models.Building.city.contains(city))
    # Parse and apply max_price filter
    if max_price not in (None, ""):
        try:
            max_price_value = float(max_price)
            query = query.filter(models.Building.price_per_m2 <= max_price_value)
        except ValueError:
            pass

    buildings_list = query.all()

    # Attach first photo path per building for display
    building_ids = [b.id for b in buildings_list]
    if building_ids:
        photos = (
            db.query(models.BuildingPhoto)
            .filter(models.BuildingPhoto.building_id.in_(building_ids))
            .all()
        )
        first_photo_by_building: dict[int, str] = {}
        allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
        for p in photos:
            # filter by allowed image extensions
            path = (p.file_path or "").lower()
            _, ext = os.path.splitext(path)
            if ext not in allowed_ext:
                continue
            if p.building_id not in first_photo_by_building:
                first_photo_by_building[p.building_id] = p.file_path
        for b in buildings_list:
            setattr(b, "image", first_photo_by_building.get(b.id))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "regions": regions_list,
            "selected_region": int(region) if region not in (None, "") and region.isdigit() else None,
            "selected_city": city,
            "selected_price": float(max_price) if max_price not in (None, "") else None,
            "buildings": buildings_list,
            "current_year": datetime.utcnow().year,
        },
    )


@app.get("/building/{building_id}", response_class=HTMLResponse)
def building_detail_page(building_id: int, request: Request, db: Session = Depends(get_db)):
    building = db.get(models.Building, building_id)
    if not building:
        return RedirectResponse(url="/", status_code=302)

    # Images
    photos = db.query(models.BuildingPhoto).filter(models.BuildingPhoto.building_id == building_id).all()
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
    images = []
    images_360 = []
    for p in photos:
        path = (p.file_path or "").lower()
        _, ext = os.path.splitext(path)
        if p.is_360:
            images_360.append(p.file_path)
        elif ext in allowed_ext:
            images.append(p.file_path)

    # Facilities (amenities)
    facilities = []
    try:
        facilities = [a.name for a in (building.amenities_rel or []) if getattr(a, "is_active", True)]
    except Exception:
        pass

    # Available spaces (rooms with status free)
    spaces = (
        db.query(models.Room)
        .filter(models.Room.building_id == building_id, models.Room.status == "free")
        .all()
    )
    available_spaces = [
        {
            "id": s.id,
            "floor": s.floor,
            "room_number": s.room_number,
            "area": s.area,
        }
        for s in spaces
    ]

    # Nearby places placeholder (inject real data if available)
    nearby_places = []

    return templates.TemplateResponse(
        "building_detail.html",
        {
            "request": request,
            "building": building,
            "images": images,
            "images_360": images_360,
            "facilities": facilities,
            "nearby_places": nearby_places,
            "available_spaces": available_spaces,
            "current_year": datetime.utcnow().year,
        },
    )


# Resident Panel
@app.get("/residentpanel", response_class=HTMLResponse)
def resident_panel(request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    buildings_list = db.query(models.Building).all()
    my_requests = (
        db.query(models.RentalRequest)
        .filter(models.RentalRequest.user_id == current_user.id)
        .order_by(models.RentalRequest.created_at.desc())
        .all()
    )
    my_contracts = (
        db.query(models.Contract)
        .filter(models.Contract.user_id == current_user.id)
        .order_by(models.Contract.created_at.desc())
        .all()
    )
    notes = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse(
        "resident_panel.html",
        {
            "request": request,
            "buildings": buildings_list,
            "requests": my_requests,
            "contracts": my_contracts,
            "notifications": notes,
            "current_user": current_user,
            "current_year": datetime.utcnow().year,
        },
    )


# Signer Panel
@app.get("/signerpanel", response_class=HTMLResponse)
def signer_panel(request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    signer = db.query(models.Signer).filter(models.Signer.email == current_user.email).first()
    approvals = []
    if signer:
        approvals = (
            db.query(models.RequestApproval)
            .filter(models.RequestApproval.signer_id == signer.id)
            .order_by(models.RequestApproval.id.desc())
            .all()
        )
    return templates.TemplateResponse(
        "signer_panel.html",
        {
            "request": request,
            "approvals": approvals,
            "signer": signer,
            "current_user": current_user,
            "current_year": datetime.utcnow().year,
        },
    )


# Create rental request
@app.post("/rental-requests")
def create_rental_request(
    request: Request,
    building_id: int = Form(...),
    selected_spaces: str = Form(...),  # JSON string
    total_price: float = Form(...),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    rr = models.RentalRequest(
        user_id=current_user.id,
        building_id=building_id,
        selected_spaces=selected_spaces,
        total_price=total_price,
        status="pending",
    )
    db.add(rr)
    db.commit()
    db.refresh(rr)

    # Determine signers chain by region
    building = db.get(models.Building, building_id)
    chain = (
        db.query(models.Signer)
        .filter((models.Signer.region_id == building.region_id) | (models.Signer.region_id.is_(None)))
        .order_by(models.Signer.signing_order.asc())
        .all()
    )
    for s in chain:
        ra = models.RequestApproval(request_id=rr.id, signer_id=s.id, status="pending")
        db.add(ra)
    db.commit()

    # Notify resident
    note = models.Notification(user_id=current_user.id, title="Request submitted", message=f"Rental request #{rr.id} submitted.")
    db.add(note)
    db.commit()
    return RedirectResponse(url="/residentpanel?msg=request_submitted", status_code=303)


# Signer actions: approve/decline
@app.post("/request-approvals/{approval_id}/approve")
def approve_request(approval_id: int, request: Request, comment: str | None = Form(None), db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    ra = db.get(models.RequestApproval, approval_id)
    if not ra:
        return RedirectResponse(url="/signerpanel?error=not_found", status_code=303)
    ra.status = "approved"
    ra.action_at = datetime.utcnow()
    if comment:
        ra.reason = comment
    db.add(ra)
    db.commit()

    # If all approvals approved -> create final Contract and notify resident
    remaining = (
        db.query(models.RequestApproval)
        .filter(models.RequestApproval.request_id == ra.request_id, models.RequestApproval.status != "approved")
        .count()
    )
    if remaining == 0:
        req = db.get(models.RentalRequest, ra.request_id)
        if req:
            req.status = "approved"
            db.add(req)
            contract = models.Contract(
                building_id=req.building_id,
                user_id=req.user_id,
                selected_rooms=req.selected_spaces,
                total_price=req.total_price,
                zero_risk=False,
                status="approved",
            )
            db.add(contract)
            db.add(models.Notification(user_id=req.user_id, title="Request approved", message=f"Your request #{req.id} is approved. Contract created."))
            db.commit()
    return RedirectResponse(url="/signerpanel?msg=approved", status_code=303)


@app.post("/request-approvals/{approval_id}/decline")
def decline_request(approval_id: int, request: Request, reason: str = Form(...), db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    ra = db.get(models.RequestApproval, approval_id)
    if not ra:
        return RedirectResponse(url="/signerpanel?error=not_found", status_code=303)
    ra.status = "declined"
    ra.reason = reason
    ra.action_at = datetime.utcnow()
    db.add(ra)
    db.commit()
    # Mark request rejected
    req = db.get(models.RentalRequest, ra.request_id)
    if req:
        req.status = "rejected"
        db.add(req)
        db.add(models.Notification(user_id=req.user_id, title="Request declined", message=f"Your request #{req.id} was declined: {reason}"))
        db.commit()
    return RedirectResponse(url="/signerpanel?msg=declined", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
        if current_user.role != "superadmin":
            return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    regions_list = db.query(models.Region).all()
    amenities_list = db.query(models.Amenity).all()
    users_list = db.query(models.User).all()
    buildings_list = db.query(models.Building).all()
    rooms_list = db.query(models.Room).all()
    photos_list = db.query(models.BuildingPhoto).all()
    contracts_list = db.query(models.Contract).all()
    approvals_list = db.query(models.Approval).all()
    signers_list = db.query(models.Signer).order_by(models.Signer.signing_order.asc()).all()

    msg = request.query_params.get("msg")
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "regions": regions_list,
            "users": users_list,
            "buildings": buildings_list,
            "rooms": rooms_list,
            "photos": photos_list,
            "amenities": amenities_list,
            "contracts": contracts_list,
            "approvals": approvals_list,
            "signers": signers_list,
            "current_year": datetime.utcnow().year,
            "msg": msg,
            "error": error,
        },
    )


def _ensure_superadmin(request: Request, db: Session) -> models.User | None:
    try:
        user = get_current_user(request, db)
        if user.role == "superadmin":
            return user
    except Exception:
        pass
    return None


def _ensure_admin_or_superadmin(request: Request, db: Session) -> models.User | None:
    try:
        user = get_current_user(request, db)
        if user.role in ("superadmin", "admin"):
            return user
    except Exception:
        pass
    return None


@app.post("/admin/amenities")
def admin_create_amenity(
    request: Request,
    name: str = Form(...),
    icon: str | None = Form(None),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_admin_or_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    existing = db.query(models.Amenity).filter(models.Amenity.name.ilike(name)).first()
    if existing:
        return RedirectResponse(url="/admin?error=amenity_exists", status_code=302)
    a = models.Amenity(name=name, icon=icon, is_active=bool(is_active))
    db.add(a)
    db.commit()
    return RedirectResponse(url="/admin?msg=amenity_created", status_code=302)


@app.post("/admin/amenities/delete")
def admin_delete_amenity(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_admin_or_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    a = db.get(models.Amenity, id)
    if not a:
        return RedirectResponse(url="/admin?error=amenity_not_found", status_code=302)
    a.is_active = False
    db.add(a)
    db.commit()
    return RedirectResponse(url="/admin?msg=amenity_deleted", status_code=302)
@app.post("/admin/regions")
def admin_create_region(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    region = models.Region(name=name)
    db.add(region)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/change-password", response_class=HTMLResponse)
def change_password_form(request: Request):
    return templates.TemplateResponse("change_password.html", {"request": request, "error": None})


@app.post("/change-password")
def change_password_submit(
    request: Request,
    email: str = Form(...),
    old_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
):
    from app.utils import verify_password, hash_password
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(old_password, user.password_hash):
        return templates.TemplateResponse("change_password.html", {"request": request, "error": "Invalid email or password"}, status_code=400)
    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/admin/signers", response_class=HTMLResponse)
def signers_page(request: Request, db: Session = Depends(get_db)):
    try:
        current_user = get_current_user(request, db)
        if current_user.role != "superadmin":
            return RedirectResponse(url="/login", status_code=302)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)

    signers_list = db.query(models.Signer).order_by(models.Signer.signing_order.asc()).all()
    msg = request.query_params.get("msg")
    error = request.query_params.get("error")
    return templates.TemplateResponse(
        "signers.html",
        {
            "request": request,
            "signers": signers_list,
            "current_year": datetime.utcnow().year,
            "msg": msg,
            "error": error,
        },
    )


@app.get("/signers", response_class=HTMLResponse)
def signers_page_alias(request: Request, db: Session = Depends(get_db)):
    return signers_page(request, db)

# Signers admin handlers
@app.post("/admin/signers")
def admin_create_signer(
    request: Request,
    name: str = Form(...),
    position: str = Form(...),
    email: str = Form(...),
    phone: str | None = Form(None),
    region_id: str | None = Form(None),
    signing_order: int = Form(...),
    status_value: str = Form("active"),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    # Normalize optional fields
    region_id_val = None
    if region_id not in (None, ""):
        try:
            region_id_val = int(region_id)
        except ValueError:
            region_id_val = None
    phone_val = phone if phone not in (None, "") else None

    if region_id_val is not None:
        existing = (
            db.query(models.Signer)
            .filter(models.Signer.region_id == region_id_val)
            .filter(models.Signer.signing_order == signing_order)
            .first()
        )
        if existing:
            return RedirectResponse(url="/signers?error=signing_order_in_use", status_code=303)
    # Ensure user account exists and has signer role
    from app.utils import hash_password
    user_acc = db.query(models.User).filter(models.User.email == email).first()
    if not user_acc:
        user_acc = models.User(
            name=name,
            email=email,
            password_hash=hash_password("12345"),
            role="signer",
            region_id=region_id_val,
        )
        db.add(user_acc)
        db.commit()
        db.refresh(user_acc)
    else:
        # add signer role if missing (CSV roles in role field)
        roles = [r.strip() for r in (user_acc.role or "").split(",") if r.strip()]
        if "signer" not in roles:
            roles.append("signer")
            user_acc.role = ",".join(roles)
            db.add(user_acc)
            db.commit()

    s = models.Signer(
        name=name,
        position=position,
        email=email,
        phone=phone_val,
        region_id=region_id_val,
        signing_order=signing_order,
        status=status_value,
    )
    db.add(s)
    db.commit()
    return RedirectResponse(url="/signers?msg=signer_created", status_code=303)


@app.post("/admin/signers/update")
def admin_update_signer(
    request: Request,
    id: int = Form(...),
    name: str | None = Form(None),
    position: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    region_id: str | None = Form(None),
    signing_order: int | None = Form(None),
    status_value: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    s = db.get(models.Signer, id)
    if not s:
        return RedirectResponse(url="/signers?error=signer_not_found", status_code=303)
    # Normalize
    region_id_val = None
    if region_id not in (None, ""):
        try:
            region_id_val = int(region_id)
        except ValueError:
            region_id_val = None
    phone_val = phone if phone not in (None, "") else None

    if signing_order is not None:
        target_region = region_id_val if region_id_val is not None else s.region_id
        if target_region is not None:
            exists = (
                db.query(models.Signer)
                .filter(models.Signer.region_id == target_region)
                .filter(models.Signer.signing_order == signing_order, models.Signer.id != id)
                .first()
            )
            if exists:
                return RedirectResponse(url="/signers?error=signing_order_in_use", status_code=303)
    if name is not None:
        s.name = name
    if position is not None:
        s.position = position
    if email is not None:
        s.email = email
    if phone is not None:
        s.phone = phone_val
    if region_id is not None:
        s.region_id = region_id_val
    if signing_order is not None:
        s.signing_order = signing_order
    if status_value is not None:
        s.status = status_value
    db.add(s)
    db.commit()
    return RedirectResponse(url="/signers?msg=signer_updated", status_code=303)


@app.post("/admin/signers/delete")
def admin_delete_signer(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    s = db.get(models.Signer, id)
    if s:
        db.delete(s)
        db.commit()
    return RedirectResponse(url="/signers?msg=signer_deleted", status_code=303)


@app.post("/signers/add")
def signers_add_alias(
    request: Request,
    name: str = Form(...),
    position: str = Form(...),
    email: str = Form(...),
    phone: str | None = Form(None),
    region_id: str | None = Form(None),
    signing_order: int = Form(...),
    status_value: str = Form("active"),
    db: Session = Depends(get_db),
):
    return admin_create_signer(request, name, position, email, phone, region_id, signing_order, status_value, db)


@app.post("/admin/regions/update")
def admin_update_region(request: Request, id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    region = db.get(models.Region, id)
    if not region:
        return RedirectResponse(url="/admin", status_code=302)
    region.name = name
    db.add(region)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/regions/delete")
def admin_delete_region(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    region = db.get(models.Region, id)
    if region:
        db.delete(region)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Users (admin)
@app.post("/admin/users")
def admin_create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    region_id: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    data_region_id = None
    if region_id not in (None, ""):
        try:
            data_region_id = int(region_id)
        except ValueError:
            data_region_id = None
    from app.utils import hash_password

    new_user = models.User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
        region_id=data_region_id,
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/users/delete")
def admin_delete_user(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    db_user = db.get(models.User, id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Buildings (admin)
@app.post("/admin/buildings")
def admin_create_building(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    region_id: int = Form(...),
    floors: int = Form(...),
    total_area: float = Form(...),
    price_per_m2: float = Form(...),
    amenity_ids: _List[int] | None = Form(None),
    images: _List[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    b = models.Building(
        name=name,
        address=address,
        city=city,
        region_id=region_id,
        floors=floors,
        total_area=total_area,
        price_per_m2=price_per_m2,
    )
    db.add(b)
    db.commit()
    # Attach selected amenities
    if amenity_ids:
        # amenity_ids from form can be a single str or list[str]
        ids = amenity_ids if isinstance(amenity_ids, list) else [amenity_ids]
        try:
            ids = [int(i) for i in ids]
        except Exception:
            ids = []
        if ids:
            selected = db.query(models.Amenity).filter(models.Amenity.id.in_(ids)).all()
            b.amenities_rel = selected
            db.add(b)
            db.commit()
    if images:
        uploads_dir = os.path.join("app", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        for file in images:
            if not file or not file.filename:
                continue
            original_name = os.path.basename(file.filename)
            base_name = original_name.replace(" ", "_")
            unique_name = f"{int(time.time()*1000)}_{base_name}"
            dst_path = os.path.join(uploads_dir, unique_name)
            with open(dst_path, "wb") as out_file:
                shutil.copyfileobj(file.file, out_file)
            rel_path = f"/uploads/{unique_name}"
            photo = models.BuildingPhoto(building_id=b.id, file_path=rel_path, is_360=False)
            db.add(photo)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/buildings/delete")
def admin_delete_building(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    b = db.get(models.Building, id)
    if b:
        db.delete(b)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Rooms (admin)
@app.post("/admin/rooms")
def admin_create_room(
    request: Request,
    building_id: int = Form(...),
    floor: int = Form(...),
    area: float = Form(...),
    status: str = Form(...),
    space_type: str = Form("room"),  # 'room' or 'floor'
    room_number: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    # Normalize: if entire floor (open space), we store room_number as None
    normalized_room_number = room_number if space_type == "room" else None
    r = models.Room(
        building_id=building_id,
        floor=floor,
        room_number=normalized_room_number,
        area=area,
        status=status,
    )
    db.add(r)
    db.commit()
    return RedirectResponse(url="/admin?msg=space_added", status_code=302)


@app.post("/admin/rooms/delete")
def admin_delete_room(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    r = db.get(models.Room, id)
    if r:
        db.delete(r)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Building Photos (admin)
@app.post("/admin/photos")
def admin_create_photo(
    request: Request,
    building_id: int = Form(...),
    file_path: str = Form(...),
    is_360: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    is_360_value = bool(is_360)
    p = models.BuildingPhoto(building_id=building_id, file_path=file_path, is_360=is_360_value)
    db.add(p)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/photos/upload")
def admin_upload_photo(
    request: Request,
    building_id: int = Form(...),
    file: UploadFile = File(...),
    is_360: str | None = Form(None),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Ensure uploads directory exists
    uploads_dir = os.path.join("app", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Generate safe unique filename
    original_name = os.path.basename(file.filename or "upload")
    base_name = original_name.replace(" ", "_")
    unique_name = f"{int(time.time()*1000)}_{base_name}"
    dst_path = os.path.join(uploads_dir, unique_name)

    # Save file to disk
    with open(dst_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    # Store relative path for serving via /uploads
    rel_path = f"/uploads/{unique_name}"
    photo = models.BuildingPhoto(building_id=building_id, file_path=rel_path, is_360=bool(is_360))
    db.add(photo)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/photos/delete")
def admin_delete_photo(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    p = db.get(models.BuildingPhoto, id)
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Contracts (admin)
@app.post("/admin/contracts")
def admin_create_contract(
    request: Request,
    building_id: int = Form(...),
    user_id: int = Form(...),
    selected_rooms: str = Form(...),
    total_price: float = Form(...),
    zero_risk: str | None = Form(None),
    zero_risk_doc: str | None = Form(None),
    status_value: str = Form("pending"),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    c = models.Contract(
        building_id=building_id,
        user_id=user_id,
        selected_rooms=selected_rooms,
        total_price=total_price,
        zero_risk=bool(zero_risk),
        zero_risk_doc=zero_risk_doc,
        status=status_value,
    )
    db.add(c)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/contracts/delete")
def admin_delete_contract(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    c = db.get(models.Contract, id)
    if c:
        db.delete(c)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


# Approvals (admin)
@app.post("/admin/approvals")
def admin_create_approval(
    request: Request,
    contract_id: int = Form(...),
    signer_id: int = Form(...),
    status_value: str = Form("pending"),
    db: Session = Depends(get_db),
):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    a = models.Approval(contract_id=contract_id, signer_id=signer_id, status=status_value)
    db.add(a)
    db.commit()
    return RedirectResponse(url="/admin", status_code=302)


@app.post("/admin/approvals/delete")
def admin_delete_approval(request: Request, id: int = Form(...), db: Session = Depends(get_db)):
    user = _ensure_superadmin(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    a = db.get(models.Approval, id)
    if a:
        db.delete(a)
        db.commit()
    return RedirectResponse(url="/admin", status_code=302)


    return RedirectResponse(url="/admin", status_code=302)
