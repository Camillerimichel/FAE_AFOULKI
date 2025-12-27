from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class Document(Base):
    __tablename__ = "Documents"

    id_document = Column(Integer, primary_key=True, index=True)
    id_filleule = Column(Integer, ForeignKey("Filleules.id_filleule"))
    id_type = Column(Integer, ForeignKey("TypesDocuments.id_type"))
    id_annee_scolaire = Column(Integer, ForeignKey("Annee_scolaire.id_annee_scolaire"))

    titre = Column(String(255))
    chemin_fichier = Column(Text)
    date_upload = Column(DateTime, default=datetime.datetime.utcnow)

    filleule = relationship("Filleule", back_populates="documents")
    type_document = relationship("TypeDocument", back_populates="documents")
    annee_scolaire_ref = relationship("AnneeScolaire", back_populates="documents")
