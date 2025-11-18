# backend/seed.py
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
from models import Categoria, Ejercicio

Base.metadata.create_all(bind=engine)
db = SessionLocal()

categorias_nombres = ["Print/Input", "If/Elif/Else", "Bucles", "Arrays", "Funcions", "POO"]
categorias_db = {}

for nombre in categorias_nombres:
    categoria = db.query(Categoria).filter(Categoria.nombre == nombre).first()
    if not categoria:
        categoria = Categoria(nombre=nombre)
        db.add(categoria)
        db.commit()
    categorias_db[nombre] = categoria

with open("exercices.json", encoding="utf-8") as f:
    ejercicios_data = json.load(f)

for ej in ejercicios_data:
    existente = db.query(Ejercicio).filter(Ejercicio.titulo == ej["titulo"]).first()
    if existente:
        continue
    categoria = categorias_db.get(ej.pop("categoria_nombre"))
    if categoria:
        ejercicio = Ejercicio(**ej, categoria_id=categoria.id)
        db.add(ejercicio)

db.commit()

print("✅ Base de datos actualizada con categorías y ejercicios.")
db.close()
