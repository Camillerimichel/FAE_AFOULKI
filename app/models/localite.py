from sqlalchemy import Column, Float, Integer, String, Text

from app.database import Base


class Localite(Base):
    __tablename__ = "Localites"

    id_localite = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    aliases = Column(Text)
