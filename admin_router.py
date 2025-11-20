from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Usuario
from dependencies import get_db, get_password_hash, require_admin


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

# 🟩 Listar usuarios
@router.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    prof = Depends(require_admin)
):
    return db.query(Usuario).all()

# 🟥 Borrar usuario
@router.delete("/usuarios/{usuario_id}")
def borrar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    prof = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado"}

# 🟦 Crear usuario
@router.post("/usuarios")
def crear_usuario(
    email: str,
    nombre: str,
    password: str,
    db: Session = Depends(get_db),
    prof = Depends(require_admin)
):
    if db.query(Usuario).filter(Usuario.nombre == nombre).first():
        raise HTTPException(status_code=400, detail="Ese nombre ya existe")

    nuevo = Usuario(
        email=email,
        nombre=nombre,
        hashed_password=get_password_hash(password),
        rol="alumno"
    )
    db.add(nuevo)
    db.commit()
    return {"mensaje": "Usuario creado", "id": nuevo.id}

# 🟨 Cambiar rol
@router.put("/usuarios/{usuario_id}/rol")
def cambiar_rol(
    usuario_id: int,
    nuevo_rol: str,
    db: Session = Depends(get_db),
    prof = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.rol = nuevo_rol
    db.commit()
    return {"mensaje": f"Rol cambiado a {nuevo_rol}"}

# 🟧 Resetear contraseña
@router.put("/usuarios/{usuario_id}/password")
def reset_password(
    usuario_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    prof = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"mensaje": "Contraseña actualizada"}
