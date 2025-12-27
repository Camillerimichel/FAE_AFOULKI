from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    id_filleule: int
    id_type: int
    id_annee_scolaire: int | None = None
    titre: Optional[str] = None
    chemin_fichier: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id_document: int
    date_upload: datetime

    class Config:
        from_attributes = True
