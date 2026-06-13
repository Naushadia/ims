from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    status: str = Field(default="active", max_length=50)

    @field_validator("full_name")
    @classmethod
    def name_stripped(cls, v: str) -> str:
        return v.strip()

    @field_validator("phone")
    @classmethod
    def phone_stripped(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("status")
    @classmethod
    def status_validate(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("active", "inactive"):
            raise ValueError("Status must be 'active' or 'inactive'")
        return v


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, max_length=50)

    @field_validator("full_name")
    @classmethod
    def name_stripped(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else None

    @field_validator("phone")
    @classmethod
    def phone_stripped(cls, v: str | None) -> str | None:
        return v.strip() if v else v

    @field_validator("status")
    @classmethod
    def status_validate(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().lower()
        if v not in ("active", "inactive"):
            raise ValueError("Status must be 'active' or 'inactive'")
        return v


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    data: list[CustomerResponse]
    count: int
