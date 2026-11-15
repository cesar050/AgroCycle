"""
Implementacion PostgreSQL del repositorio de catalogo Tipos de Actividad.
El acceso a datos (SQL) vive aqui, en infraestructura, no en las rutas.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.i_tipo_actividad_repository import ITipoActividadRepository


class PgTipoActividadRepository(ITipoActividadRepository):

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self) -> List[dict]:
        resultados = self.db.execute(
            text(
                "SELECT id, nombre, descripcion "
                "FROM tipos_actividad "
                "WHERE activo = true "
                "ORDER BY id"
            )
        ).fetchall()

        return [
            {
                "id": r.id,
                "nombre": r.nombre,
                "descripcion": r.descripcion,
            }
            for r in resultados
        ]
