from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Correspondant(Base):
    __tablename__ = "Correspondants"

    id_correspondant = Column(Integer, primary_key=True, index=True)

    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    telephone = Column(String(50))
    email = Column(String(255))
    lien = Column(String(255))

    filleules = relationship("Filleule", back_populates="correspondant")
