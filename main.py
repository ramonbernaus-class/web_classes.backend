# backend/main.py
import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os

import models
import database

# Importamos las dependencias ya desacopladas
from dependencies import (
    get_db,
    get_current_user,
    create_access_token,
    verify_password,
    get_password_hash
)

# Importamos el router de administración
from admin_router import router as admin_router

# Crear tablas si no existen
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Añadir router de administración
app.include_router(admin_router)

# Configuración CORS
origins = [
    "https://classesrepasramon.netlify.app",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Pydantic Models --------

from pydantic import BaseModel

class UsuarioCreate(BaseModel):
    email: str
    nombre: str
    password: str

class LoginRequest(BaseModel):
    nombre: str
    password: str

class EntregaCreate(BaseModel):
    usuario_id: int
    ejercicio_id: int
    codigo: str

# -------- ENDPOINTS --------

@app.get("/api/categorias/{categoria_id}")
def leer_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria


@app.get("/api/categorias")
def leer_categorias(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    return db.query(models.Categoria).all()


@app.get("/api/ejercicios")
def leer_ejercicios(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    return db.query(models.Ejercicio).all()


@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.nombre == request.nombre).first()

    if not usuario or not verify_password(request.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({
        "sub": str(usuario.id),
        "nombre": usuario.nombre,
        "rol": usuario.rol
    })

    return {
        "access_token": token,
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "rol": usuario.rol
        }
    }


@app.post("/api/usuarios")
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Evitar duplicados por nombre
    if db.query(models.Usuario).filter(models.Usuario.nombre == usuario.nombre).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    hashed = get_password_hash(usuario.password)

    nuevo_usuario = models.Usuario(
        email=usuario.email,
        nombre=usuario.nombre,
        hashed_password=hashed,
        rol="alumno"   
    )

    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {"mensaje": "Usuario creado", "usuario": {"id": nuevo_usuario.id, "nombre": nuevo_usuario.nombre}}


@app.post("/api/entregas")
def crear_entrega(
    entrega: EntregaCreate,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    nueva = models.Entrega(
        usuario_id=usuario.id,
        ejercicio_id=entrega.ejercicio_id,
        codigo=entrega.codigo,
        fecha_envio=datetime.utcnow()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"mensaje": "Entrega guardada", "entrega_id": nueva.id}


@app.get("/api/entregas")
def listar_entregas(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user)
):
    entregas = db.query(models.Entrega).all()
    return [
        {
            "id": e.id,
            "usuario": e.usuario.nombre,
            "ejercicio": e.ejercicio.titulo,
            "fecha_envio": e.fecha_envio,
        }
        for e in entregas
    ]

