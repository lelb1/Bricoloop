from typing import Literal

from pydantic import BaseModel, ConfigDict

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
