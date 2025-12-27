from pydantic import BaseModel
from typing import Optional

class CorrespondantBase(BaseModel):
    nom: str
    prenom: str
    telephone: Optional[str] = None
    email: Optional[str] = None
    lien: Optional[str] = None

class CorrespondantCreate(CorrespondantBase):
    pass

class CorrespondantResponse(CorrespondantBase):
    id_correspondant: int

    class Config:
        from_attributes = True
