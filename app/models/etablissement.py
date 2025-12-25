from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

ETABLISSEMENT_TYPES = (
    "primaire",
    "secondaire",
    "collège",
    "lycée",
    "université",
    "école post bac",
)

class Etablissement(Base):
    __tablename__ = "Etablissements"

    id_etablissement = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    adresse = Column(Text)
    ville = Column(String(255))
    type = Column(String(100))

    scolarites = relationship("Scolarite", back_populates="etablissement")
    filleules = relationship("Filleule", back_populates="etablissement")
