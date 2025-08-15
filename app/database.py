from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema():
    """Lightweight schema guard for SQLite to add missing columns when models evolve.
    Avoids full migration tooling for small MVP.
    """
    try:
        with engine.connect() as conn:
            # Add created_at to building_photos if missing
            info = conn.exec_driver_sql("PRAGMA table_info('building_photos')").fetchall()
            columns = {row[1] for row in info}  # (cid, name, type, ...)
            if 'created_at' not in columns:
                conn.exec_driver_sql("ALTER TABLE building_photos ADD COLUMN created_at DATETIME")
            # Add missing columns to amenities
            info_am = conn.exec_driver_sql("PRAGMA table_info('amenities')").fetchall()
            am_cols = {row[1] for row in info_am}
            if 'icon' not in am_cols:
                conn.exec_driver_sql("ALTER TABLE amenities ADD COLUMN icon VARCHAR")
            if 'is_active' not in am_cols:
                conn.exec_driver_sql("ALTER TABLE amenities ADD COLUMN is_active BOOLEAN DEFAULT 1")
            if 'created_at' not in am_cols:
                conn.exec_driver_sql("ALTER TABLE amenities ADD COLUMN created_at DATETIME")
            if 'updated_at' not in am_cols:
                conn.exec_driver_sql("ALTER TABLE amenities ADD COLUMN updated_at DATETIME")
            
            # Add missing columns to signers
            try:
                info_sig = conn.exec_driver_sql("PRAGMA table_info('signers')").fetchall()
                sig_cols = {row[1] for row in info_sig}
                if 'created_at' not in sig_cols:
                    conn.exec_driver_sql("ALTER TABLE signers ADD COLUMN created_at DATETIME")
                if 'updated_at' not in sig_cols:
                    conn.exec_driver_sql("ALTER TABLE signers ADD COLUMN updated_at DATETIME")
            except Exception:
                pass  # Table might not exist yet
                
            # Add missing columns to contract_signatures
            try:
                info_cs = conn.exec_driver_sql("PRAGMA table_info('contract_signatures')").fetchall()
                cs_cols = {row[1] for row in info_cs}
                if 'signed_at' not in cs_cols:
                    conn.exec_driver_sql("ALTER TABLE contract_signatures ADD COLUMN signed_at DATETIME")
                if 'decline_reason' not in cs_cols:
                    conn.exec_driver_sql("ALTER TABLE contract_signatures ADD COLUMN decline_reason TEXT")
            except Exception:
                pass  # Table might not exist yet
                
    except Exception:
        # Best-effort; continue if not SQLite or on error
        pass
