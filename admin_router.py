from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import models
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

# 🟦 Estadísticas del sistema
@router.get("/estadisticas")
def estadisticas(db: Session = Depends(get_db), admin = Depends(require_admin)):

    total_usuarios = db.query(Usuario).count()
    total_admins = db.query(Usuario).filter(Usuario.rol == "admin").count()
    total_alumnos = db.query(Usuario).filter(Usuario.rol == "alumno").count()

    total_categorias = db.query(models.Categoria).count()
    total_ejercicios = db.query(models.Ejercicio).count()
    total_entregas = db.query(models.Entrega).count()

    # últimas 5 entregas
    entregas = db.query(models.Entrega)\
        .order_by(models.Entrega.fecha_envio.desc())\
        .limit(5)\
        .all()

    ultimas = [
        {
            "usuario": e.usuario.nombre,
            "ejercicio": e.ejercicio.titulo,
            "fecha_envio": e.fecha_envio.isoformat(),
        } for e in entregas
    ]

    return {
        "usuarios": total_usuarios,
        "admins": total_admins,
        "alumnos": total_alumnos,
        "categorias": total_categorias,
        "ejercicios": total_ejercicios,
        "entregas": total_entregas,
        "ultimas_entregas": ultimas
    }
