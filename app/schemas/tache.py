from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TacheBase(BaseModel):
    titre: str
    description: Optional[str] = None
    objet_id: int
    statut: str
    date_debut: date
    date_fin: Optional[date] = None
    cible_type: str
    cible_id: Optional[int] = None
    assignee_ids: list[int] = Field(default_factory=list)


class TacheCreate(TacheBase):
    pass


class TacheUpdate(TacheBase):
    pass


class TacheResponse(TacheBase):
    id_tache: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TacheCommentCreate(BaseModel):
    content: str
    author_id: Optional[int] = None
