from sqlalchemy import Column, Integer, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class SuiviSocial(Base):
    __tablename__ = "SuiviSocial"

    id_suivi = Column(Integer, primary_key=True, index=True)
    id_filleule = Column(Integer, ForeignKey("Filleules.id_filleule"))

    date_suivi = Column(Date)
    commentaire = Column(Text)
    besoins = Column(Text)

    filleule = relationship("Filleule", back_populates="suivis")
