from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class Parrainage(Base):
    __tablename__ = "Parrainages"

    id_parrainage = Column(Integer, primary_key=True, index=True)
    id_filleule = Column(Integer, ForeignKey("Filleules.id_filleule"))
    id_parrain = Column(Integer, ForeignKey("Parrains.id_parrain"))

    date_debut = Column(Date)
    date_fin = Column(Date)
    statut = Column(String(100))
    bourse_centre = Column(Integer)
    bourse_rw = Column(Integer)

    filleule = relationship("Filleule", back_populates="parrainages")
    parrain = relationship("Parrain", back_populates="parrainages")
