# backend/admin_ejercicios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import models
from dependencies import get_db, require_admin

router = APIRouter(
    prefix="/api/admin/ejercicios",
    tags=["Admin-Ejercicios"]
)

# --- Pydantic models for input
class EjercicioCreate(BaseModel):
    titulo: str
    enunciado: Optional[str] = ""
    solucion: Optional[str] = ""
    dificultad: Optional[str] = "fácil"
    lenguaje: Optional[str] = "Python"
    categoria_id: Optional[int] = None
    subcategoria: Optional[str] = None

class EjercicioUpdate(BaseModel):
    titulo: Optional[str] = None
    enunciado: Optional[str] = None
    solucion: Optional[str] = None
    dificultad: Optional[str] = None
    lenguaje: Optional[str] = None
    categoria_id: Optional[int] = None
    subcategoria: Optional[str] = None

# --- Listar ejercicios (con filtros opcionales y opcional paginación)
@router.get("", response_model=List[models.Ejercicio])
def listar_ejercicios(
    categoria_id: Optional[int] = None,
    dificultad: Optional[str] = None,
    subcategoria: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    q = db.query(models.Ejercicio)
    if categoria_id:
        q = q.filter(models.Ejercicio.categoria_id == categoria_id)
    if dificultad:
        q = q.filter(models.Ejercicio.dificultad == dificultad)
    if subcategoria:
        q = q.filter(models.Ejercicio.subcategoria == subcategoria)
    ejercicios = q.order_by(models.Ejercicio.id.desc()).offset(skip).limit(limit).all()
    return ejercicios

# --- Obtener un ejercicio por id
@router.get("/{ejercicio_id}")
def obtener_ejercicio(ejercicio_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return e

# --- Crear ejercicio
@router.post("/")
def crear_ejercicio(payload: EjercicioCreate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    if not payload.titulo or payload.titulo.strip() == "":
        raise HTTPException(status_code=400, detail="El título es obligatorio")

    nuevo = models.Ejercicio(
        titulo=payload.titulo.strip(),
        enunciado=payload.enunciado or "",
        solucion=payload.solucion or "",
        dificultad=payload.dificultad or "fácil",
        lenguaje=payload.lenguaje or "Python",
        categoria_id=payload.categoria_id,
        subcategoria=payload.subcategoria
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"mensaje": "Ejercicio creado", "id": nuevo.id}

# --- Editar ejercicio
@router.put("/{ejercicio_id}")
def editar_ejercicio(ejercicio_id: int, payload: EjercicioUpdate, db: Session = Depends(get_db), admin = Depends(require_admin)):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(e, field, value)
    db.commit()
    return {"mensaje": "Ejercicio actualizado"}

# --- Borrar ejercicio
@router.delete("/{ejercicio_id}")
def borrar_ejercicio(ejercicio_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    db.delete(e)
    db.commit()
    return {"mensaje": "Ejercicio eliminado"}

# --- Duplicar ejercicio
@router.post("/{ejercicio_id}/duplicar")
def duplicar_ejercicio(ejercicio_id: int, db: Session = Depends(get_db), admin = Depends(require_admin)):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    clon = models.Ejercicio(
        titulo=f"{e.titulo} (copia)",
        enunciado=e.enunciado,
        solucion=e.solucion,
        dificultad=e.dificultad,
        lenguaje=e.lenguaje,
        categoria_id=e.categoria_id,
        subcategoria=e.subcategoria
    )
    db.add(clon)
    db.commit()
    db.refresh(clon)
    return {"mensaje": "Ejercicio duplicado", "id": clon.id}
