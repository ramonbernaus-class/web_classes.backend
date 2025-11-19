# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import Categoria, Ejercicio, Entrega, Usuario
from typing import List
import sys
import os
import models
import database
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()



origins = [
    "https://celadon-kashata-ec3aa3.netlify.app",
    "http://localhost:5173",  # vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# ✅ Endpoint para TODAS las categorías
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if usuario is None:
        raise credentials_exception

    return usuario


# ✅ Endpoint para UNA categoría por ID
@app.get("/api/categorias/{categoria_id}")
def leer_categoria(
    categoria_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    categoria = db.query(models.Categoria).filter(models.Categoria.id == categoria_id).first()
    if categoria is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return categoria

@app.get("/api/ejercicios")
def leer_ejercicios(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return db.query(models.Ejercicio).all()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    password = password[:72] 
    return pwd_context.hash(password)

@app.get("/api/categorias")
def leer_categorias(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return db.query(models.Categoria).all()
@app.post("/api/login")

def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.nombre == request.nombre).first()
    if not usuario or not verify_password(request.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_access_token(data={"sub": str(usuario.id), "nombre": usuario.nombre})
    return {
        "access_token": token, 
        "usuario": {
            "id": usuario.id, 
            "nombre": usuario.nombre, 
        }
    }

@app.post("/api/usuarios")
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.nombre == usuario.nombre).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    hashed = get_password_hash(usuario.password)
    nuevo_usuario = Usuario(
        email=usuario.email,
        nombre=usuario.nombre,
        hashed_password=hashed
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return {"mensaje": "Usuario creado", "usuario": {"id": nuevo_usuario.id, "nombre": nuevo_usuario.nombre}}

@app.post("/api/entregas")
def crear_entrega(entrega: EntregaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    nueva = Entrega(
        usuario_id=entrega.usuario_id,
        ejercicio_id=entrega.ejercicio_id,
        codigo=entrega.codigo,
        fecha_envio=datetime.utcnow()
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {"mensaje": "Entrega guardada", "entrega_id": nueva.id}

@app.get("/api/entregas")
def listar_entregas(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    entregas = db.query(Entrega).all()
    return [
        {
            "id": e.id,
            "usuario": e.usuario.nombre,
            "ejercicio": e.ejercicio.titulo,
            "fecha_envio": e.fecha_envio,
        } for e in entregas
    ]
