from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Correspondant(Base):
    __tablename__ = "Correspondants"

    id_correspondant = Column(Integer, primary_key=True, index=True)
    id_filleule = Column(Integer, ForeignKey("Filleules.id_filleule"))

    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    telephone = Column(String(50))
    email = Column(String(255))
    lien = Column(String(255))

    filleule = relationship("Filleule", back_populates="correspondants")
