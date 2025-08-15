from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Text, DateTime, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String)  # superadmin, admin, resident, signer
    region_id = Column(Integer, ForeignKey("regions.id"))

    # Relationships
    region = relationship("Region", back_populates="users")
    contracts = relationship("Contract", back_populates="user")
    approvals_given = relationship("Approval", back_populates="signer")

class Region(Base):
    __tablename__ = "regions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)

    # Relationships
    users = relationship("User", back_populates="region")
    buildings = relationship("Building", back_populates="region")

class Building(Base):
    __tablename__ = "buildings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    city = Column(String)
    region_id = Column(Integer, ForeignKey("regions.id"))
    floors = Column(Integer)
    total_area = Column(Float)
    price_per_m2 = Column(Float)
    amenities = Column(Text)

    # Relationships
    region = relationship("Region", back_populates="buildings")
    rooms = relationship("Room", back_populates="building")
    photos = relationship("BuildingPhoto", back_populates="building")
    amenities_rel = relationship("Amenity", secondary="building_amenities", back_populates="buildings")
    contracts = relationship("Contract", back_populates="building")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    floor = Column(Integer)
    room_number = Column(String)
    area = Column(Float)
    status = Column(String)  # free, booked

    # Relationships
    building = relationship("Building", back_populates="rooms")

class BuildingPhoto(Base):
    __tablename__ = "building_photos"
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    file_path = Column(String)
    is_360 = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    building = relationship("Building", back_populates="photos")


# Association table for many-to-many between buildings and amenities
building_amenities = Table(
    "building_amenities",
    Base.metadata,
    Column("building_id", Integer, ForeignKey("buildings.id"), primary_key=True),
    Column("amenity_id", Integer, ForeignKey("amenities.id"), primary_key=True),
)


class Amenity(Base):
    __tablename__ = "amenities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    icon = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    buildings = relationship("Building", secondary="building_amenities", back_populates="amenities_rel")

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    selected_rooms = Column(Text)  # JSON строка с id комнат
    total_price = Column(Float)
    zero_risk = Column(Boolean, default=False)
    zero_risk_doc = Column(Text)  # Zero Risk order number (if any)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    building = relationship("Building", back_populates="contracts")
    user = relationship("User", back_populates="contracts")
    approvals = relationship("Approval", back_populates="contract")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    signer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, approved, rejected
    approved_at = Column(DateTime)

    # Relationships
    contract = relationship("Contract", back_populates="approvals")
    signer = relationship("User", back_populates="approvals_given")


class Signer(Base):
    __tablename__ = "signers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    position = Column(String)
    email = Column(String)
    phone = Column(String)
    region_id = Column(Integer, ForeignKey("regions.id"))
    signing_order = Column(Integer)
    status = Column(String, default="active")  # active / inactive
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    region = relationship("Region")


class ContractSignature(Base):
    __tablename__ = "contract_signatures"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    signer_id = Column(Integer, ForeignKey("signers.id"))
    status = Column(String, default="pending")  # pending / approved / declined
    signed_at = Column(DateTime)
    decline_reason = Column(Text)

    # Relationships
    contract = relationship("Contract")
    signer = relationship("Signer")


class RentalRequest(Base):
    __tablename__ = "rental_requests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    building_id = Column(Integer, ForeignKey("buildings.id"))
    selected_spaces = Column(Text)  # JSON of selected floors/rooms
    total_price = Column(Float)
    status = Column(String, default="pending")  # pending, in_progress, approved, rejected
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    building = relationship("Building")


class RequestApproval(Base):
    __tablename__ = "request_approvals"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("rental_requests.id"))
    signer_id = Column(Integer, ForeignKey("signers.id"))
    status = Column(String, default="pending")  # pending/approved/declined
    action_at = Column(DateTime)
    reason = Column(Text)

    request = relationship("RentalRequest")
    signer = relationship("Signer")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
