# backend/crear_usuario.py
from database import SessionLocal
from models import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()
usuario = Usuario(
    email="tu@email.com",
    nombre="Tu Nombre",
    hashed_password=pwd_context.hash("tu_contraseña_segura")
)
db.add(usuario)
db.commit()
print("Usuario creado")