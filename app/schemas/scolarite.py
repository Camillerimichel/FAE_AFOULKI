from pydantic import BaseModel
from typing import Optional

class ScolariteBase(BaseModel):
    id_filleule: int
    id_etablissement: int
    annee_scolaire: Optional[str] = None
    niveau: Optional[str] = None
    filiere: Optional[str] = None
    section: Optional[str] = None
    sous_groupe: Optional[str] = None
    responsable_concours: Optional[str] = None
    referent_a: Optional[str] = None
    referent_b: Optional[str] = None
    resultats: Optional[str] = None
    diplome_obtenu: Optional[str] = None

class ScolariteCreate(ScolariteBase):
    pass

class ScolariteResponse(ScolariteBase):
    id_scolarite: int

    class Config:
        orm_mode = True
