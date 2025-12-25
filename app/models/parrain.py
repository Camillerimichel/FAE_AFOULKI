from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Parrain(Base):
    __tablename__ = "Parrains"

    id_parrain = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    email = Column(String(255))
    telephone = Column(String(50))
    adresse = Column(Text)
    photo = Column(String(255))

    parrainages = relationship("Parrainage", back_populates="parrain")
