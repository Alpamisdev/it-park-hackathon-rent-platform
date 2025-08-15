from app.database import SessionLocal
from app import models
from app.utils import hash_password


def main():
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == "admin@mail.com").first()
        if existing:
            # Ensure correct role and reset password hash to pbkdf2 version
            existing.name = "Admin"
            existing.role = "superadmin"
            existing.password_hash = hash_password("12345")
            db.add(existing)
            db.commit()
            print("Superadmin ensured/updated: admin@mail.com / 12345")
            return
        user = models.User(
            name="Admin",
            email="admin@mail.com",
            password_hash=hash_password("12345"),
            role="superadmin",
            region_id=None,
        )
        db.add(user)
        db.commit()
        print("Superadmin created: admin@mail.com / 12345")
    finally:
        db.close()


if __name__ == "__main__":
    main()


