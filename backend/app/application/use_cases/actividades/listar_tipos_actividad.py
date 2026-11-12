"""
Caso de uso: Listar Tipos de Actividad del catalogo.
Expone los tipos de actividad disponibles para registrar labores.
"""
from app.domain.repositories.i_tipo_actividad_repository import ITipoActividadRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class ListarTiposActividadUseCase:

    def __init__(self, tipo_actividad_repository: ITipoActividadRepository):
        self.repo = tipo_actividad_repository

    @log_caso_de_uso('listar_tipos_actividad')
    def ejecutar(self) -> list:
        """Retorna la lista de tipos de actividad activos."""
        return self.repo.listar_activos()
