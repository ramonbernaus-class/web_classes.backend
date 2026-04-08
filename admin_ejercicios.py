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

# =========================================================
# Helpers
# =========================================================

def normalizar_dificultad(valor: Optional[str]) -> str:
    """
    Normaliza la dificultad para aceptar variantes con/sin tilde.
    Valores finales recomendados:
    - fácil
    - medio
    - difícil
    """
    if not valor:
        return "fácil"

    v = valor.strip().lower()

    mapa = {
        "facil": "fácil",
        "fácil": "fácil",
        "medio": "medio",
        "dificil": "difícil",
        "difícil": "difícil"
    }

    return mapa.get(v, "fácil")


def limpiar_texto(valor: Optional[str], default: Optional[str] = "") -> Optional[str]:
    """
    Devuelve string limpio o default.
    Permite devolver None en campos opcionales como subcategoria.
    """
    if valor is None:
        return default
    return str(valor)


# =========================================================
# Pydantic models
# =========================================================

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


# =========================================================
# Listar ejercicios
# =========================================================

@router.get("/")
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
        q = q.filter(models.Ejercicio.dificultad == normalizar_dificultad(dificultad))

    if subcategoria:
        q = q.filter(models.Ejercicio.subcategoria == subcategoria)

    return q.order_by(models.Ejercicio.id.desc()).offset(skip).limit(limit).all()





# =========================================================
# Crear ejercicio
# =========================================================

@router.post("/")
def crear_ejercicio(
    payload: EjercicioCreate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    if not payload.titulo or payload.titulo.strip() == "":
        raise HTTPException(status_code=400, detail="El título es obligatorio")

    nuevo = models.Ejercicio(
        titulo=payload.titulo.strip(),
        enunciado=limpiar_texto(payload.enunciado, ""),
        solucion=limpiar_texto(payload.solucion, ""),
        dificultad=normalizar_dificultad(payload.dificultad),
        lenguaje=limpiar_texto(payload.lenguaje, "Python"),
        categoria_id=payload.categoria_id,
        subcategoria=limpiar_texto(payload.subcategoria, None)
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {
        "mensaje": "Ejercicio creado",
        "id": nuevo.id
    }


# =========================================================
# Importar varios ejercicios de golpe
# =========================================================

@router.post("/importar-lote")
def importar_ejercicios_lote(
    payload: List[EjercicioCreate],
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Importación parcial real:
    - Si un ejercicio falla, los demás se siguen intentando.
    - Se hace commit por cada ejercicio válido.
    """
    if not payload or len(payload) == 0:
        raise HTTPException(status_code=400, detail="No se han enviado ejercicios")

    ejercicios_creados = []
    errores = []

    for i, item in enumerate(payload):
        try:
            if not item.titulo or item.titulo.strip() == "":
                errores.append({
                    "index": i,
                    "titulo": None,
                    "error": "El título es obligatorio"
                })
                continue

            nuevo = models.Ejercicio(
                titulo=item.titulo.strip(),
                enunciado=limpiar_texto(item.enunciado, ""),
                solucion=limpiar_texto(item.solucion, ""),
                dificultad=normalizar_dificultad(item.dificultad),
                lenguaje=limpiar_texto(item.lenguaje, "Python"),
                categoria_id=item.categoria_id,
                subcategoria=limpiar_texto(item.subcategoria, None)
            )

            db.add(nuevo)
            db.commit()
            db.refresh(nuevo)

            ejercicios_creados.append({
                "index": i,
                "id": nuevo.id,
                "titulo": nuevo.titulo
            })

        except Exception as e:
            db.rollback()
            errores.append({
                "index": i,
                "titulo": getattr(item, "titulo", None),
                "error": str(e)
            })

    return {
        "mensaje": "Importación completada",
        "insertados": len(ejercicios_creados),
        "errores": len(errores),
        "ejercicios_creados": ejercicios_creados,
        "detalle_errores": errores
    }

# =========================================================
# Obtener un ejercicio por id
# =========================================================

@router.get("/{ejercicio_id}")
def obtener_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()

    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    return e


# =========================================================
# Editar ejercicio
# =========================================================

@router.put("/{ejercicio_id}")
def editar_ejercicio(
    ejercicio_id: int,
    payload: EjercicioUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()

    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    data = payload.dict(exclude_unset=True)

    # Validación especial para título si viene informado
    if "titulo" in data:
        if data["titulo"] is None or str(data["titulo"]).strip() == "":
            raise HTTPException(status_code=400, detail="El título no puede estar vacío")
        data["titulo"] = str(data["titulo"]).strip()

    # Normalizar dificultad si se actualiza
    if "dificultad" in data:
        data["dificultad"] = normalizar_dificultad(data["dificultad"])

    # Limpiar campos de texto opcionales si vienen
    if "enunciado" in data:
        data["enunciado"] = limpiar_texto(data["enunciado"], "")
    if "solucion" in data:
        data["solucion"] = limpiar_texto(data["solucion"], "")
    if "lenguaje" in data:
        data["lenguaje"] = limpiar_texto(data["lenguaje"], "Python")
    if "subcategoria" in data:
        data["subcategoria"] = limpiar_texto(data["subcategoria"], None)

    for field, value in data.items():
        setattr(e, field, value)

    db.commit()

    return {"mensaje": "Ejercicio actualizado"}


# =========================================================
# Borrar ejercicio
# =========================================================

@router.delete("/{ejercicio_id}")
def borrar_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    e = db.query(models.Ejercicio).filter(models.Ejercicio.id == ejercicio_id).first()

    if not e:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")

    db.delete(e)
    db.commit()

    return {"mensaje": "Ejercicio eliminado"}


# =========================================================
# Duplicar ejercicio
# =========================================================

@router.post("/{ejercicio_id}/duplicar")
def duplicar_ejercicio(
    ejercicio_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
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

    return {
        "mensaje": "Ejercicio duplicado",
        "id": clon.id
    }