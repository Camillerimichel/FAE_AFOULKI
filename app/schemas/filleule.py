from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class FilleuleBase(BaseModel):
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    village: Optional[str] = None
    ville: Optional[str] = None
    telephone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    etat_civil: Optional[str] = None
    annee_rentree: Optional[str] = None
    etablissement_id: Optional[int] = None
    photo: Optional[str] = None

class FilleuleCreate(FilleuleBase):
    pass

class FilleuleResponse(FilleuleBase):
    id_filleule: int
    date_creation: datetime

    class Config:
        from_attributes = True
