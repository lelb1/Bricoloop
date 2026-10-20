from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["Perçage", "Jardinage", "Peinture", "Nettoyage", "Mesure", "Autre"]
ToolStatus = Literal["available", "lent", "unavailable"]


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    firstName: str
    district: str


class Tool(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ownerId: int
    name: str
    category: Category
    etat: str | None = None
    description: str | None = None
    status: ToolStatus = "available"


class ToolDetail(Tool):
    owner: User


class ToolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=2, max_length=60, description="Nom obligatoire : 2 à 60 caractères"
    )
    category: Category = Field(description="Catégorie parmi les six valeurs autorisées")
    description: str | None = Field(
        default=None, max_length=300, description="Description facultative : 300 caractères maximum"
    )

    etat: str | None = Field(default=None, max_length=300, description="État physique de l’outil")

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class ToolEtatUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    etat: str | None = Field(..., max_length=300)


class LoanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    startDate: date
    endDate: date

    @field_validator("startDate", "endDate", mode="before")
    @classmethod
    def require_iso_date(cls, value):
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Date attendue au format AAAA-MM-JJ")
        return date.fromisoformat(value)


class Loan(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    toolId: int
    borrowerId: int
    startDate: date
    endDate: date
    status: Literal["pending", "accepted", "refused", "returned"]
