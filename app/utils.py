from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str):
    # TEMPORAL: Comparación de contraseña en texto plano
    # TODO: Cambiar a bcrypt en producción
    return password == hashed
