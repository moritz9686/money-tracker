"""Financial-account API contracts."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    account_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    card_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    currency: str = Field(default="INR", min_length=3, max_length=3)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    bank_name: str | None
    account_last4: str | None
    card_last4: str | None
    currency: str
