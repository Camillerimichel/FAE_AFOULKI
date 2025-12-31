import datetime

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base

TASK_STATUSES = ("A faire", "En cours", "En attente", "Realise")
TASK_OBJECTS = (
    "demande_info",
    "demande_document",
    "demande_entretien",
    "demande_aide_sociale",
    "preparation_remise_bourses",
    "attribution_bourses",
    "relance_dons",
    "envoi_email",
    "autre",
)
TASK_TARGETS = ("filleule", "correspondant", "parrain", "backoffice", "fae", "autre")


class TaskAssignee(Base):
    __tablename__ = "task_assignees"

    task_id = Column(
        Integer,
        ForeignKey("Taches.id_tache", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Tache(Base):
    __tablename__ = "Taches"

    id_tache = Column(Integer, primary_key=True, index=True)
    titre = Column(String(255), nullable=False)
    description = Column(Text)
    objet = Column(Enum(*TASK_OBJECTS, name="tache_objet"), nullable=False)
    statut = Column(Enum(*TASK_STATUSES, name="tache_statut"), nullable=False, default="A faire")
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date)
    cible_type = Column(Enum(*TASK_TARGETS, name="tache_cible_type"), nullable=False)
    cible_id = Column(Integer)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    created_by = relationship("User", foreign_keys=[created_by_id])
    assignees = relationship("User", secondary="task_assignees", back_populates="tasks")
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at",
    )

    @property
    def assignee_ids(self) -> list[int]:
        return [user.id for user in self.assignees]


class TaskComment(Base):
    __tablename__ = "task_comments"

    id_comment = Column(Integer, primary_key=True, index=True)
    task_id = Column(
        Integer,
        ForeignKey("Taches.id_tache", ondelete="CASCADE"),
        nullable=False,
    )
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("Tache", back_populates="comments")
    author = relationship("User", back_populates="task_comments")
