from app.domain.repositories.i_tipo_suelo_repository import ITipoSueloRepository


class ListarTiposSueloUseCase:
    """Catalogo de tipos de suelo para los formularios de Parcela."""

    def __init__(self, tipo_suelo_repository: ITipoSueloRepository):
        self.tipo_suelo_repository = tipo_suelo_repository

    def ejecutar(self) -> list:
        return self.tipo_suelo_repository.listar_activos()
