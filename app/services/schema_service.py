from sqlalchemy import text

from app.database import DB_NAME, engine


def ensure_filleule_photo_column():
    query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Filleules'
          AND COLUMN_NAME = 'photo'
        """
    )

    with engine.begin() as conn:
        count = conn.execute(query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Filleules ADD COLUMN photo VARCHAR(255)"))
