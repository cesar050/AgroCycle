from datetime import date, timedelta
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository
from app.infrastructure.external.copernicus.copernicus_service import obtener_ndvi_bbox


class ObtenerNdviFincaUseCase:
    """
    Pide a Copernicus (Sentinel-2 L2A, via Sentinel Hub WMS) la imagen
    NDVI recortada al bounding box de las parcelas de la finca.
    """

    def __init__(
        self,
        finca_repository: IFincaRepository,
        mapa_query_repository: IMapaQueryRepository
    ):
        self.finca_repository = finca_repository
        self.mapa_query_repository = mapa_query_repository

    def ejecutar(self, finca_id: str, agricultor_id: str, fecha: str = None) -> bytes:
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("Finca no encontrada")

        bbox = self.mapa_query_repository.obtener_bbox_parcelas(finca_id)
        if not bbox:
            return None

        if not fecha:
            # Margen de 10 dias para dar tiempo a la revisita de Sentinel-2 (~5 dias)
            fecha = (date.today() - timedelta(days=10)).isoformat()

        return obtener_ndvi_bbox(bbox, fecha)
