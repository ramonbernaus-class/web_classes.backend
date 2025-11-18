# backend/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# ------------------ Categorías ------------------
class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)

    ejercicios = relationship("Ejercicio", back_populates="categoria")

# ------------------ Ejercicios ------------------
class Ejercicio(Base):
    __tablename__ = "ejercicios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    enunciado = Column(Text)
    solucion = Column(Text)
    dificultad = Column(String)  # "fácil", "media", "difícil"
    lenguaje = Column(String)    # "Python", "Java", etc.
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    subcategoria = Column(String, nullable=True)  # ej: "for", "while", "ambos"

    categoria = relationship("Categoria", back_populates="ejercicios")
    entregas = relationship("Entrega", back_populates="ejercicio")

# ------------------ Usuarios ------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String) 
    nombre = Column(String, unique=True, index=True)  
    hashed_password = Column(String)

    entregas = relationship("Entrega", back_populates="usuario")

# ------------------ Entregas ------------------
class Entrega(Base):
    __tablename__ = "entregas"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"))
    codigo = Column(Text, nullable=False)
    fecha_envio = Column(DateTime, default=datetime.utcnow)
    resultado = Column(String, nullable=True)

    usuario = relationship("Usuario")
    ejercicio = relationship("Ejercicio")

