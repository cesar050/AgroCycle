from app.domain.repositories.i_parcela_repository import IParcelaRepository
from app.domain.repositories.i_lote_repository import ILoteRepository
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository
from app.infrastructure.external.topografia_service import generar_puntos_dentro_poligono


class ObtenerGrillaTopograficaUseCase:
    """
    Util de desarrollo: retorna el poligono real de una parcela y la
    grilla de puntos generada dentro de el, en formato GeoJSON listo
    para pegar en geojson.io. Antes no verificaba propietario; ahora
    sube la cadena parcela -> lote -> finca -> agricultor.
    """

    def __init__(
        self,
        parcela_repository: IParcelaRepository,
        lote_repository: ILoteRepository,
        finca_repository: IFincaRepository,
        mapa_query_repository: IMapaQueryRepository
    ):
        self.parcela_repository = parcela_repository
        self.lote_repository = lote_repository
        self.finca_repository = finca_repository
        self.mapa_query_repository = mapa_query_repository

    def ejecutar(self, parcela_id: str, agricultor_id: str) -> dict:
        parcela = self.parcela_repository.buscar_por_id(parcela_id)
        if not parcela:
            raise ValueError("Parcela no encontrada")

        lote = self.lote_repository.buscar_por_id(parcela.lote_id)
        if not lote:
            raise ValueError("Parcela no encontrada")

        finca = self.finca_repository.buscar_por_id(lote.finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para ver esta parcela")

        datos = self.mapa_query_repository.obtener_geometria_parcela(parcela_id)
        if not datos or not datos['geojson']:
            raise ValueError("Parcela sin geometria registrada")

        coordenadas = datos['geojson']['coordinates'][0]
        puntos = generar_puntos_dentro_poligono(
            [[p[0], p[1]] for p in coordenadas],
            datos['superficie_ha']
        )

        features = [{
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": datos['geojson']['coordinates']
            },
            "properties": {
                "nombre": datos['nombre'],
                "superficie_ha": datos['superficie_ha'],
                "tipo": "parcela"
            }
        }]

        for i, (lat, lng) in enumerate(puntos):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lng, lat]},
                "properties": {"numero": i + 1, "tipo": "punto_grilla"}
            })

        return {
            "type": "FeatureCollection",
            "features": features,
            "total_puntos": len(puntos)
        }
