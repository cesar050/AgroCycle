from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository


class ObtenerParcelasGeojsonUseCase:
    """
    Retorna todas las parcelas activas de una finca con su geometria
    GeoJSON simple (sin agrupar por lote). Antes era SQL crudo directo
    en la ruta, sin verificar propietario; ahora exige que la finca
    pertenezca al agricultor autenticado.
    """

    def __init__(
        self,
        finca_repository: IFincaRepository,
        mapa_query_repository: IMapaQueryRepository
    ):
        self.finca_repository = finca_repository
        self.mapa_query_repository = mapa_query_repository

    def ejecutar(self, finca_id: str, agricultor_id: str) -> list:
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise ValueError("Finca no encontrada")

        return self.mapa_query_repository.listar_parcelas_geojson_simple(finca_id)
