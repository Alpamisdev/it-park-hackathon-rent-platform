from passlib.context import CryptContext


# Prefer pbkdf2_sha256 to avoid external bcrypt backend issues
password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return password_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return password_context.verify(plain_password, password_hash)
    except Exception:
        return False
