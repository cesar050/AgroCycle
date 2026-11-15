from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository


class ObtenerMapaFincaUseCase:
    """
    Ensambla la estructura finca -> lotes -> parcelas con geometria
    GeoJSON para el visor de Mapa General. Antes vivia como SQL crudo
    directo en la ruta; aqui se verifica ademas que la finca pertenezca
    al agricultor que la solicita (la ruta original no lo hacia).
    """

    def __init__(
        self,
        finca_repository: IFincaRepository,
        mapa_query_repository: IMapaQueryRepository
    ):
        self.finca_repository = finca_repository
        self.mapa_query_repository = mapa_query_repository

    def ejecutar(self, finca_id: str, agricultor_id: str) -> dict:
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise ValueError("Finca no encontrada")

        finca_data = self.mapa_query_repository.obtener_finca_con_geojson(finca_id)
        if not finca_data:
            raise ValueError("Finca no encontrada")

        lotes = self.mapa_query_repository.listar_lotes_con_geojson(finca_id)
        parcelas = self.mapa_query_repository.listar_parcelas_con_estado(finca_id)

        parcelas_por_lote: dict = {}
        for p in parcelas:
            parcelas_por_lote.setdefault(p['lote_id'], []).append({
                'id': p['id'],
                'nombre': p['nombre'],
                'superficie_ha': p['superficie_ha'],
                'altitud_msnm': p['altitud_msnm'],
                'pendiente': p['pendiente'],
                'orientacion': p['orientacion'],
                'estado_fenologico': p['estado_fenologico'],
                'avance_ciclo': p['avance_ciclo'],
                'produccion_real': p['produccion_real'],
                'estimacion_qq_ha': p['estimacion_qq_ha'],
                'geojson': p['geojson'],
            })

        for lote in lotes:
            lote['parcelas'] = parcelas_por_lote.get(lote['id'], [])

        return {
            'finca': {
                'id': finca_data['id'],
                'nombre': finca_data['nombre'],
                'superficie_ha': finca_data['superficie_ha'],
                'provincia': finca_data['provincia'],
                'canton': finca_data['canton'],
                'sector': finca_data['sector'],
                'geojson': finca_data['geojson'],
                'lotes': lotes,
            }
        }
