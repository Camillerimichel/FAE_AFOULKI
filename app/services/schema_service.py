from sqlalchemy import text

from app.database import DB_NAME, engine
from app.models.etablissement import ETABLISSEMENT_TYPES


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


def ensure_parrain_photo_column():
    query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Parrains'
          AND COLUMN_NAME = 'photo'
        """
    )

    with engine.begin() as conn:
        count = conn.execute(query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Parrains ADD COLUMN photo VARCHAR(255)"))


def ensure_filleule_etablissement_column():
    column_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Filleules'
          AND COLUMN_NAME = 'etablissement_id'
        """
    )

    fk_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Filleules'
          AND COLUMN_NAME = 'etablissement_id'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    old_fk_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Correspondants'
          AND COLUMN_NAME = 'id_filleule'
        """
    )
    old_fk_names_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Correspondants'
          AND COLUMN_NAME = 'id_filleule'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    with engine.begin() as conn:
        count = conn.execute(column_query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Filleules ADD COLUMN etablissement_id INT NULL"))

        fk_exists = conn.execute(fk_query, {"db": DB_NAME}).fetchone()
        if fk_exists:
            return

        conn.execute(
            text(
                """
                UPDATE Filleules f
                LEFT JOIN Etablissements e
                  ON f.etablissement_id = e.id_etablissement
                SET f.etablissement_id = NULL
                WHERE f.etablissement_id IS NOT NULL
                  AND e.id_etablissement IS NULL
                """
            )
        )

        conn.execute(
            text(
                """
                ALTER TABLE Filleules
                ADD CONSTRAINT fk_filleules_etablissement
                FOREIGN KEY (etablissement_id)
                REFERENCES Etablissements(id_etablissement)
                ON DELETE SET NULL
                """
            )
        )


def ensure_etablissement_type_enum():
    query = text(
        """
        SELECT COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Etablissements'
          AND COLUMN_NAME = 'type'
        """
    )

    def sql_quote(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    values_sql = ", ".join([sql_quote(value) for value in ETABLISSEMENT_TYPES])
    desired = f"enum({values_sql})"

    with engine.begin() as conn:
        row = conn.execute(query, {"db": DB_NAME}).fetchone()
        if not row:
            return
        column_type = (row[0] or "").lower()
        if column_type == desired:
            return

        conn.execute(
            text(
                f"UPDATE Etablissements SET `type` = NULL WHERE `type` IS NOT NULL AND `type` NOT IN ({values_sql})"
            )
        )
        conn.execute(text(f"ALTER TABLE Etablissements MODIFY COLUMN `type` ENUM({values_sql}) NULL"))


def ensure_scolarite_annee_scolaire_column():
    column_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Scolarite'
          AND COLUMN_NAME = 'id_annee_scolaire'
        """
    )

    fk_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Scolarite'
          AND COLUMN_NAME = 'id_annee_scolaire'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    with engine.begin() as conn:
        count = conn.execute(column_query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Scolarite ADD COLUMN id_annee_scolaire INT NULL"))

        fk_exists = conn.execute(fk_query, {"db": DB_NAME}).fetchone()
        if fk_exists:
            return

        conn.execute(
            text(
                """
                UPDATE Scolarite s
                INNER JOIN Annee_scolaire a
                  ON s.annee_scolaire = a.periode
                SET s.id_annee_scolaire = a.id_annee_scolaire
                WHERE s.id_annee_scolaire IS NULL
                """
            )
        )

        conn.execute(
            text(
                """
                ALTER TABLE Scolarite
                ADD CONSTRAINT fk_scolarite_annee_scolaire
                FOREIGN KEY (id_annee_scolaire)
                REFERENCES Annee_scolaire(id_annee_scolaire)
                ON DELETE SET NULL
                """
            )
        )


def ensure_filleule_correspondant_column():
    column_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Filleules'
          AND COLUMN_NAME = 'id_correspondant'
        """
    )

    fk_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Filleules'
          AND COLUMN_NAME = 'id_correspondant'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    old_fk_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Correspondants'
          AND COLUMN_NAME = 'id_filleule'
        """
    )
    old_fk_names_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Correspondants'
          AND COLUMN_NAME = 'id_filleule'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    with engine.begin() as conn:
        count = conn.execute(column_query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Filleules ADD COLUMN id_correspondant INT NULL"))

        has_old_fk = conn.execute(old_fk_query, {"db": DB_NAME}).scalar()
        if has_old_fk:
            conn.execute(
                text(
                    """
                    UPDATE Filleules f
                    INNER JOIN Correspondants c
                      ON c.id_filleule = f.id_filleule
                    SET f.id_correspondant = c.id_correspondant
                    WHERE f.id_correspondant IS NULL
                    """
                )
            )
            constraints = conn.execute(old_fk_names_query, {"db": DB_NAME}).fetchall()
            for row in constraints:
                if row and row[0]:
                    conn.execute(text(f"ALTER TABLE Correspondants DROP FOREIGN KEY `{row[0]}`"))
            conn.execute(text("ALTER TABLE Correspondants DROP COLUMN id_filleule"))

        fk_exists = conn.execute(fk_query, {"db": DB_NAME}).fetchone()
        if fk_exists:
            return

        conn.execute(
            text(
                """
                ALTER TABLE Filleules
                ADD CONSTRAINT fk_filleules_correspondant
                FOREIGN KEY (id_correspondant)
                REFERENCES Correspondants(id_correspondant)
                ON DELETE SET NULL
                """
            )
        )


def ensure_document_annee_scolaire_column():
    column_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Documents'
          AND COLUMN_NAME = 'id_annee_scolaire'
        """
    )

    fk_query = text(
        """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'Documents'
          AND COLUMN_NAME = 'id_annee_scolaire'
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """
    )

    with engine.begin() as conn:
        count = conn.execute(column_query, {"db": DB_NAME}).scalar()
        if count == 0:
            conn.execute(text("ALTER TABLE Documents ADD COLUMN id_annee_scolaire INT NULL"))

        fk_exists = conn.execute(fk_query, {"db": DB_NAME}).fetchone()
        if fk_exists:
            return

        conn.execute(
            text(
                """
                ALTER TABLE Documents
                ADD CONSTRAINT fk_documents_annee_scolaire
                FOREIGN KEY (id_annee_scolaire)
                REFERENCES Annee_scolaire(id_annee_scolaire)
                ON DELETE SET NULL
                """
            )
        )


def ensure_user_password_reset_columns():
    hash_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'reset_token_hash'
        """
    )

    expires_query = text(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = :db
          AND TABLE_NAME = 'users'
          AND COLUMN_NAME = 'reset_token_expires'
        """
    )

    with engine.begin() as conn:
        hash_count = conn.execute(hash_query, {"db": DB_NAME}).scalar()
        if hash_count == 0:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_hash VARCHAR(255) NULL"))

        expires_count = conn.execute(expires_query, {"db": DB_NAME}).scalar()
        if expires_count == 0:
            conn.execute(text("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME NULL"))
