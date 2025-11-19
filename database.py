# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Cargar variables de entorno (solo necesario en local)
load_dotenv()

# Leer DATABASE_URL desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear motor de PostgreSQL (Neon)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # mantiene la conexión activa y evita fallos
)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()
