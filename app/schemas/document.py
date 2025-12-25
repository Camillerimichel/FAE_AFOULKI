from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentBase(BaseModel):
    id_filleule: int
    id_type: int
    titre: Optional[str] = None
    chemin_fichier: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id_document: int
    date_upload: datetime

    class Config:
        orm_mode = True
