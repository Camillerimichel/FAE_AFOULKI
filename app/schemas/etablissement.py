from pydantic import BaseModel
from typing import Optional

class EtablissementBase(BaseModel):
    nom: str
    adresse: Optional[str] = None
    ville: Optional[str] = None
    type: Optional[str] = None

class EtablissementCreate(EtablissementBase):
    pass

class EtablissementResponse(EtablissementBase):
    id_etablissement: int

    class Config:
        orm_mode = True
