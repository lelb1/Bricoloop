from typing import Literal

from pydantic import BaseModel

Category = Literal["Perçage", "Jardinage", "Peinture", "Nettoyage", "Mesure", "Autre"]
ToolStatus = Literal["available", "lent", "unavailable"]


class User(BaseModel):
    id: int
    firstName: str
    district: str


class Tool(BaseModel):
    id: int
    ownerId: int
    name: str
    category: Category
    description: str = ""
    status: ToolStatus = "available"


class ToolDetail(Tool):
    owner: User
