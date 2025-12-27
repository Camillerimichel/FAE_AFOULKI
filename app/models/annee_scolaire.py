from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class AnneeScolaire(Base):
    __tablename__ = "Annee_scolaire"

    id_annee_scolaire = Column(Integer, primary_key=True, index=True)
    periode = Column(String(9), nullable=False)

    scolarites = relationship("Scolarite", back_populates="annee_scolaire_ref")
    documents = relationship("Document", back_populates="annee_scolaire_ref")
