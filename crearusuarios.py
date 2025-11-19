from database import SessionLocal
from models import Usuario
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def crear_usuario(email, nombre, contraseña):
    db = SessionLocal()
    try:
        usuario = Usuario(
            email=email,
            nombre=nombre,
            hashed_password=pwd_context.hash(contraseña)
        )
        db.add(usuario)
        db.commit()
        print(f"Usuario '{nombre}' creado correctamente.")
    except Exception as e:
        db.rollback()
        print("Error al crear el usuario:", e)
    finally:
        db.close()


# EJEMPLO: modifica estos datos según necesites
crear_usuario(
    email="profesor@webclases.com",
    nombre="admin",
    contraseña="admin"  
)
