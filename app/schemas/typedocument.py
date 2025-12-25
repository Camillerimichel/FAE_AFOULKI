from pydantic import BaseModel
from typing import Optional

class TypeDocumentBase(BaseModel):
    libelle: str
    description: Optional[str] = None

class TypeDocumentCreate(TypeDocumentBase):
    pass

class TypeDocumentResponse(TypeDocumentBase):
    id_type: int

    class Config:
        orm_mode = True
