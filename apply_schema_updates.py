from WebApp import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()

    # Add columns to bookings if they don't exist
    try:
        # Check information_schema for existing columns (portable approach)
        db_name = conn.execute(text("SELECT DATABASE() AS dbname")).scalar()
        for col in ("check_in_time", "check_out_time"):
            exists = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'bookings' AND COLUMN_NAME = :col"
                ),
                {"db": db_name, "col": col},
            ).scalar()
            if not exists:
                conn.execute(
                    text(f"ALTER TABLE bookings ADD COLUMN {col} DATETIME NULL;")
                )
                print(f"Added column bookings.{col}")
            else:
                print(f"Column bookings.{col} already exists")
    except Exception as e:
        print("Error adding booking columns:", e)

    # Create audit_logs table if not exists
    try:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    booking_id INT NULL,
                    action VARCHAR(120) NOT NULL,
                    details TEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
                """
            )
        )
        print("Ensured audit_logs table")
    except Exception as e:
        print("Error creating audit_logs:", e)

    # Create permissions and role_permissions tables if not exists
    try:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS permissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL UNIQUE,
                    description TEXT NULL
                ) ENGINE=InnoDB;
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    role_name VARCHAR(80) NOT NULL,
                    permission VARCHAR(120) NOT NULL
                ) ENGINE=InnoDB;
                """
            )
        )
        print("Ensured permissions and role_permissions tables")
    except Exception as e:
        print("Error creating permission tables:", e)

    conn.close()
    print("Schema update complete")
