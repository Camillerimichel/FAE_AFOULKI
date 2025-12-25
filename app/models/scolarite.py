from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Scolarite(Base):
    __tablename__ = "Scolarite"

    id_scolarite = Column(Integer, primary_key=True, index=True)
    id_filleule = Column(Integer, ForeignKey("Filleules.id_filleule"))
    id_etablissement = Column(Integer, ForeignKey("Etablissements.id_etablissement"))

    annee_scolaire = Column(String(20))
    niveau = Column(String(100))
    filiere = Column(String(255))
    section = Column(String(100))
    sous_groupe = Column(String(20))
    responsable_concours = Column(String(255))
    referent_a = Column(String(255))
    referent_b = Column(String(255))
    resultats = Column(Text)
    diplome_obtenu = Column(String(255))

    filleule = relationship("Filleule", back_populates="scolarites")
    etablissement = relationship("Etablissement", back_populates="scolarites")
