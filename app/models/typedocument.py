from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base

class TypeDocument(Base):
    __tablename__ = "TypesDocuments"

    id_type = Column(Integer, primary_key=True, index=True)
    libelle = Column(String(255), nullable=False)
    description = Column(Text)

    documents = relationship("Document", back_populates="type_document")
