"""
Configuracion de la base de datos con SQLALchemy.
Centraliza la conexion y el modelo base para todos los modelos ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os 

# URL de conexion a PostgreSQL con PostGIS 
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:cesar2026@db:5432/agrocycle'
)

# Motor de base de datos con pool de conexiones 
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True 
)

# Fabrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Clase base para todos los modelos ORM
Base = declarative_base()

def get_db():
    """
    Generador que provee una sesion de base de datos.
    Garantiza que la sesion se cierre correctamente al finalizar.
    Usado como dependencia en los casos de uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
