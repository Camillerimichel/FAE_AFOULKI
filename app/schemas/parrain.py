from pydantic import BaseModel
from typing import Optional

class ParrainBase(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None

class ParrainCreate(ParrainBase):
    pass

class ParrainResponse(ParrainBase):
    id_parrain: int

    class Config:
        orm_mode = True
