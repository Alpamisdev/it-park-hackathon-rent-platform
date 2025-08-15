from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Users
class UserBase(ORMBase):
    name: str
    email: str
    password_hash: str
    role: str
    region_id: Optional[int] = None


class UserCreate(UserBase):
    pass


class UserUpdate(ORMBase):
    name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    role: Optional[str] = None
    region_id: Optional[int] = None


class UserRead(UserBase):
    id: int


# Regions
class RegionBase(ORMBase):
    name: str


class RegionCreate(RegionBase):
    pass


class RegionUpdate(ORMBase):
    name: Optional[str] = None


class RegionRead(RegionBase):
    id: int


# Buildings
class BuildingBase(ORMBase):
    name: str
    address: str
    city: str
    region_id: int
    floors: int
    total_area: float
    price_per_m2: float
    amenities: Optional[str] = None


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(ORMBase):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region_id: Optional[int] = None
    floors: Optional[int] = None
    total_area: Optional[float] = None
    price_per_m2: Optional[float] = None
    amenities: Optional[str] = None


class BuildingRead(BuildingBase):
    id: int


# Amenities
class AmenityBase(ORMBase):
    name: str
    icon: Optional[str] = None
    is_active: bool = True


class AmenityCreate(AmenityBase):
    pass


class AmenityRead(AmenityBase):
    id: int


# Building photos
class BuildingPhotoBase(ORMBase):
    building_id: int
    file_path: str
    is_360: bool = False


class BuildingPhotoCreate(BuildingPhotoBase):
    pass


class BuildingPhotoUpdate(ORMBase):
    building_id: Optional[int] = None
    file_path: Optional[str] = None
    is_360: Optional[bool] = None


class BuildingPhotoRead(BuildingPhotoBase):
    id: int


# Rooms
class RoomBase(ORMBase):
    building_id: int
    floor: int
    room_number: str
    area: float
    status: str


class RoomCreate(RoomBase):
    pass


class RoomUpdate(ORMBase):
    building_id: Optional[int] = None
    floor: Optional[int] = None
    room_number: Optional[str] = None
    area: Optional[float] = None
    status: Optional[str] = None


class RoomRead(RoomBase):
    id: int


# Contracts
class ContractBase(ORMBase):
    building_id: int
    user_id: int
    selected_rooms: str
    total_price: float
    zero_risk: bool = False
    zero_risk_doc: Optional[str] = None
    status: str = "pending"


class ContractCreate(ContractBase):
    pass


class ContractUpdate(ORMBase):
    building_id: Optional[int] = None
    user_id: Optional[int] = None
    selected_rooms: Optional[str] = None
    total_price: Optional[float] = None
    zero_risk: Optional[bool] = None
    zero_risk_doc: Optional[str] = None
    status: Optional[str] = None


class ContractRead(ContractBase):
    id: int
    created_at: Optional[datetime] = None


# Approvals
class ApprovalBase(ORMBase):
    contract_id: int
    signer_id: int
    status: str = "pending"
    approved_at: Optional[datetime] = None


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalUpdate(ORMBase):
    contract_id: Optional[int] = None
    signer_id: Optional[int] = None
    status: Optional[str] = None
    approved_at: Optional[datetime] = None


class ApprovalRead(ApprovalBase):
    id: int


# Signers
class SignerBase(ORMBase):
    name: str
    position: str
    email: str
    phone: Optional[str] = None
    region_id: Optional[int] = None
    signing_order: int
    status: str = "active"


class SignerCreate(SignerBase):
    pass


class SignerUpdate(ORMBase):
    name: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    region_id: Optional[int] = None
    signing_order: Optional[int] = None
    status: Optional[str] = None


class SignerRead(SignerBase):
    id: int


class ContractSignatureBase(ORMBase):
    contract_id: int
    signer_id: int
    status: str = "pending"
    decline_reason: Optional[str] = None


class ContractSignatureCreate(ContractSignatureBase):
    pass


class ContractSignatureRead(ContractSignatureBase):
    id: int
    signed_at: Optional[datetime] = None


# Rental Requests
class RentalRequestBase(ORMBase):
    user_id: int
    building_id: int
    selected_spaces: str
    total_price: float
    status: str = "pending"


class RentalRequestCreate(RentalRequestBase):
    pass


class RentalRequestRead(RentalRequestBase):
    id: int
    created_at: Optional[datetime] = None


class RequestApprovalBase(ORMBase):
    request_id: int
    signer_id: int
    status: str = "pending"
    reason: Optional[str] = None


class RequestApprovalCreate(RequestApprovalBase):
    pass


class RequestApprovalRead(RequestApprovalBase):
    id: int
    action_at: Optional[datetime] = None


class NotificationBase(ORMBase):
    user_id: int
    title: str
    message: str
    is_read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationRead(NotificationBase):
    id: int
    created_at: Optional[datetime] = None
