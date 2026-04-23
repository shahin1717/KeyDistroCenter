from app.models.db import SessionLocal, User
from app.core.security import encrypt_private_key_value
from sqlalchemy import text


def main() -> None:
    db = SessionLocal()
    try:
        type_rows = db.execute(
            text(
                """
                SELECT COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME IN ('private_key_d', 'private_key_n')
                """
            )
        ).fetchall()

        col_types = {row[0]: row[1].lower() for row in type_rows}
        if col_types.get("private_key_d") in {"int", "bigint", "smallint", "tinyint", "mediumint"}:
            raise RuntimeError(
                "users.private_key_d/private_key_n are numeric columns. "
                "Run ALTER TABLE to VARCHAR(255) before migration."
            )

        users = db.query(User).all()
        updated = 0

        for user in users:
            d_val = str(user.private_key_d)
            n_val = str(user.private_key_n)

            if d_val.startswith("enc:") and n_val.startswith("enc:"):
                continue

            user.private_key_d = encrypt_private_key_value(int(d_val))
            user.private_key_n = encrypt_private_key_value(int(n_val))
            updated += 1

        db.commit()
        print(f"Private keys migration completed. Updated users: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
