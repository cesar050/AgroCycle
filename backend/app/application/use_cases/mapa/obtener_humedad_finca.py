from app.domain.repositories.i_finca_repository import IFincaRepository
from app.domain.repositories.i_mapa_query_repository import IMapaQueryRepository
from app.infrastructure.external.openmeteo.openmeteo_service import obtener_humedad_suelo
from app.application.use_cases.mapa.calcular_ks_suelo import CalcularKsSueloUseCase


class ObtenerHumedadFincaUseCase:
    """
    Para cada parcela de la finca, consulta la humedad de suelo actual
    (Open-Meteo, centroide de la parcela) y deriva el coeficiente de
    estres hidrico bidireccional (Ks_deficit, Ks_exceso, Ks_final) via
    CalcularKsSueloUseCase, para el visor de Mapa de Humedad.
    """

    def __init__(
        self,
        finca_repository: IFincaRepository,
        mapa_query_repository: IMapaQueryRepository
    ):
        self.finca_repository = finca_repository
        self.mapa_query_repository = mapa_query_repository
        self.calculadora_ks = CalcularKsSueloUseCase()

    def ejecutar(self, finca_id: str, agricultor_id: str) -> list:
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("Finca no encontrada")

        filas = self.mapa_query_repository.listar_centroides_parcelas(finca_id)

        resultado = []
        for fila in filas:
            if fila['lat'] is None or fila['lng'] is None:
                continue

            humedad = obtener_humedad_suelo(fila['lat'], fila['lng'])
            if humedad is None:
                continue

            normalizado = max(0.0, min(1.0, humedad / 0.5))
            ks = self.calculadora_ks.calcular(humedad, fila['tipo_suelo_id'])

            resultado.append({
                'parcela_id': fila['id'],
                'nombre': fila['nombre'],
                'humedad_m3m3': round(humedad, 3),
                'normalizado': round(normalizado, 3),
                **ks,
            })

        return resultado
