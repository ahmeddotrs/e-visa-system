from enum import Enum
from typing import List

from pydantic import BaseModel, EmailStr, field_validator
from sqlmodel import Field, Relationship, SQLModel


class StatusEnum(str, Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    is_admin: bool = Field(default=False)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    applications: List["VisaApplication"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_length(cls, current_password: str) -> str:
        if len(current_password) < 6:
            raise ValueError("Password must be atleast 6 characters long")
        return current_password


class UserRead(UserBase):
    id: int


class VisaApplicationBase(SQLModel):
    passport_number: str
    destination_country: str


class VisaApplication(VisaApplicationBase, table=True):
    id: str | None = Field(default=None, primary_key=True)
    status: StatusEnum = Field(default=StatusEnum.pending)

    user_id: int = Field(foreign_key="user.id")
    user: User | None = Relationship(back_populates="applications")


class VisaApplicationCreate(VisaApplicationBase):
    pass


class VisaApplicationRead(VisaApplicationBase):
    id: int
    status: StatusEnum
    user_id: int
