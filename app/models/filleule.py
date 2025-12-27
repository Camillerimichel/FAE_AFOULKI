from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Filleule(Base):
    __tablename__ = "Filleules"

    id_filleule = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    date_naissance = Column(Date)
    village = Column(String(255))
    ville = Column(String(255))
    telephone = Column(String(50))
    whatsapp = Column(String(50))
    email = Column(String(255))
    etat_civil = Column(String(100))
    annee_rentree = Column(String(20))
    etablissement_id = Column(Integer, ForeignKey("Etablissements.id_etablissement"))
    id_correspondant = Column(Integer, ForeignKey("Correspondants.id_correspondant"))
    photo = Column(String(255))
    date_creation = Column(DateTime, default=datetime.datetime.utcnow)

    parrainages = relationship("Parrainage", back_populates="filleule")
    scolarites = relationship("Scolarite", back_populates="filleule")
    correspondant = relationship("Correspondant", back_populates="filleules")
    documents = relationship("Document", back_populates="filleule")
    suivis = relationship("SuiviSocial", back_populates="filleule")
    etablissement = relationship("Etablissement", back_populates="filleules")
