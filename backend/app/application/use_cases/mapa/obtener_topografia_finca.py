from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository
from app.infrastructure.external.topografia_service import (
    generar_puntos_dentro_poligono,
    consultar_altitudes
)


class ObtenerTopografiaFincaUseCase:
    """
    Para cada parcela de la finca, genera una grilla de puntos dentro
    de su poligono real y consulta elevaciones NASA SRTM (OpenTopoData)
    para poder pintar el choropleth de pendiente/elevacion del visor
    de Mapa de Topografia.
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

        parcelas = self.mapa_query_repository.listar_parcelas_geojson_simple(finca_id)

        resultado = []
        for parcela in parcelas:
            geojson = parcela['geojson']
            if not geojson:
                continue

            coords = geojson['coordinates'][0]
            puntos = generar_puntos_dentro_poligono(
                [[c[0], c[1]] for c in coords],
                parcela['superficie_ha'] or 0.5
            )
            if not puntos:
                continue

            altitudes = consultar_altitudes(puntos)
            if not altitudes:
                continue

            alt_min = min(altitudes)
            alt_max = max(altitudes)
            rango = alt_max - alt_min or 1

            puntos_con_elev = []
            for i, (lat, lng) in enumerate(puntos):
                if i < len(altitudes):
                    elev = altitudes[i]
                    norm = (elev - alt_min) / rango
                    puntos_con_elev.append({
                        'lat': lat,
                        'lng': lng,
                        'elevacion': elev,
                        'normalizado': round(norm, 3),
                    })

            resultado.append({
                'parcela_id': parcela['id'],
                'nombre': parcela['nombre'],
                'superficie_ha': parcela['superficie_ha'],
                'altitud_min': alt_min,
                'altitud_max': alt_max,
                'altitud_prom': parcela['altitud_msnm'],
                'pendiente': parcela['pendiente'],
                'puntos': puntos_con_elev,
                'geojson': geojson,
            })

        return resultado
