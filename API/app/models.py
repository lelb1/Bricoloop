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

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value
