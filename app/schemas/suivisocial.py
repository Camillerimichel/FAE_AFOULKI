from pydantic import BaseModel
from typing import Optional
from datetime import date

class SuiviSocialBase(BaseModel):
    id_filleule: int
    date_suivi: Optional[date] = None
    commentaire: Optional[str] = None
    besoins: Optional[str] = None

class SuiviSocialCreate(SuiviSocialBase):
    pass

class SuiviSocialResponse(SuiviSocialBase):
    id_suivi: int

    class Config:
        orm_mode = True
