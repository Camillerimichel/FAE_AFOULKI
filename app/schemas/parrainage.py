from pydantic import BaseModel
from typing import Optional
from datetime import date

class ParrainageBase(BaseModel):
    id_filleule: int
    id_parrain: int
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    statut: Optional[str] = None
    bourse_centre: Optional[int] = None
    bourse_rw: Optional[int] = None

class ParrainageCreate(ParrainageBase):
    pass

class ParrainageResponse(ParrainageBase):
    id_parrainage: int

    class Config:
        orm_mode = True
