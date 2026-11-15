from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.i_tipo_suelo_repository import ITipoSueloRepository


class PgTipoSueloRepository(ITipoSueloRepository):
    """
    Catalogo de solo lectura — tipos_suelo no se crea/edita/elimina
    desde la aplicacion, por eso no tiene domain entity ni casos de
    uso de escritura, solo este repositorio de consulta.
    """

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self) -> List[dict]:
        rows = self.db.execute(text("""
            SELECT id, nombre, descripcion
            FROM tipos_suelo
            WHERE activo = TRUE
            ORDER BY id
        """)).fetchall()

        return [
            {'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion}
            for r in rows
        ]
