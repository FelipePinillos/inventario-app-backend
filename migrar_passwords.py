import sys
sys.path.append(".")

from app.database import SessionLocal
from app.models.usuario import Usuario
from app.utils import hash_password

db = SessionLocal()

usuarios = db.query(Usuario).all()

for u in usuarios:
    print(f"Migrando usuario: {u.nombre}...")
    u.contrasena = hash_password(u.contrasena)

db.commit()
db.close()

print("✅ Todas las contraseñas fueron encriptadas correctamente")