from sqlalchemy import text
from sqlalchemy.orm import Session
from app.domain.entities.estimacion import Estimacion
from app.domain.repositories.i_estimacion_repository import IEstimacionRepository
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.ml.fao33_calculator import FAO33Calculator
from app.infrastructure.logging.logger import log_caso_de_uso


class GenerarEstimacionUseCase:

    def __init__(
        self,
        db: Session,
        estimacion_repo: IEstimacionRepository,
        temporada_parcela_repo: ITemporadaParcelaRepository,
    ):
        self.db = db
        self.estimacion_repo = estimacion_repo
        self.temporada_parcela_repo = temporada_parcela_repo
        self.calculador = FAO33Calculator(db)

    @log_caso_de_uso("CU-EST-001 Generar Estimación FAO-33")
    def ejecutar(self, temporada_parcela_id: str, agricultor_id: str) -> tuple:

        datos = self._obtener_datos_completos(temporada_parcela_id, agricultor_id)

        if not datos:
            return {
                'error': 'Temporada de parcela no encontrada o no pertenece al agricultor'
            }, 404

        if not datos['fecha_siembra']:
            return {
                'error': 'La parcela no tiene fecha de siembra configurada.'
            }, 400

        resultado = self.calculador.calcular(
            temporada_parcela_id=temporada_parcela_id,
            produccion_potencial_qq_ha=float(datos['produccion_potencial_qq_ha']),
            ciclo_vegetativo_dias=int(datos['ciclo_vegetativo_dias']),
            superficie_ha=float(datos['superficie_ha']),
            pendiente_porcentaje=float(datos['pendiente_porcentaje']) if datos['pendiente_porcentaje'] else None,
        )

        estimacion = Estimacion(
            temporada_parcela_id=temporada_parcela_id,
            valor_qq_ha=resultado['valor_qq_ha'],
            valor_total_qq=resultado['valor_total_qq'],
            margen_error_porcentaje=resultado['margen_error_porcentaje'],
            algoritmo_usado='fao33',
            etapa_fenologica_momento=datos['estado_fenologico'],
            dias_desde_siembra_momento=datos['dias_desde_siembra'],
            variables_entrada=resultado['variables_entrada'],
            factores_positivos=resultado['factores_positivos'],
            factores_negativos=resultado['factores_negativos'],
        )
        estimacion.calcular_rango()

        estimacion_guardada = self.estimacion_repo.guardar(estimacion)

        return {
            'id': estimacion_guardada.id,
            'temporada_parcela_id': temporada_parcela_id,
            'parcela_nombre': datos['parcela_nombre'],
            'variedad': datos['variedad_nombre'],
            'algoritmo': 'FAO-33 (Stewart, 1977)',
            'estimacion': {
                'valor_qq_ha': estimacion_guardada.valor_qq_ha,
                'valor_total_qq': estimacion_guardada.valor_total_qq,
                'rango_minimo_qq_ha': estimacion_guardada.valor_minimo_qq_ha,
                'rango_maximo_qq_ha': estimacion_guardada.valor_maximo_qq_ha,
                'margen_error_porcentaje': estimacion_guardada.margen_error_porcentaje,
            },
            'contexto': {
                'etapa_fenologica': datos['estado_fenologico'],
                'dias_desde_siembra': datos['dias_desde_siembra'],
                'superficie_ha': float(datos['superficie_ha']),
                'pendiente_porcentaje': float(datos['pendiente_porcentaje']) if datos['pendiente_porcentaje'] else None,
                'ks_global': resultado['variables_entrada'].get('ks_global_ponderado'),
                'dias_con_datos': resultado['variables_entrada'].get('dias_con_datos'),
            },
            'factores_positivos': resultado['factores_positivos'],
            'factores_negativos': resultado['factores_negativos'],
            'detalle_por_etapa': resultado['etapas_detalle'],
            'fecha_generacion': estimacion_guardada.fecha_generacion.isoformat() if estimacion_guardada.fecha_generacion else None,
        }, 200

    def _obtener_datos_completos(
        self, temporada_parcela_id: str, agricultor_id: str
    ) -> dict:
        sql = text("""
            SELECT
                tp.id                               AS tp_id,
                tp.estado_fenologico,
                tp.dias_desde_siembra,
                tp.fecha_siembra,
                p.nombre                            AS parcela_nombre,
                p.superficie_ha,
                p.pendiente_porcentaje,
                vs.nombre                           AS variedad_nombre,
                vs.produccion_potencial_qq_ha,
                vs.ciclo_vegetativo_dias
            FROM temporada_parcelas tp
            JOIN parcelas p
                ON tp.parcela_id = p.id
            JOIN temporadas t
                ON tp.temporada_id = t.id
            JOIN agricultores a
                ON t.agricultor_id = a.id
            LEFT JOIN variedades_semilla vs
                ON tp.variedad_semilla_id = vs.id
            WHERE tp.id = CAST(:tp_id AS uuid)
              AND a.usuario_id = CAST(:agricultor_id AS uuid)
        """)

        row = self.db.execute(sql, {
            'tp_id': temporada_parcela_id,
            'agricultor_id': agricultor_id,
        }).fetchone()

        if not row:
            return None

        return {
            'tp_id': str(row.tp_id),
            'estado_fenologico': row.estado_fenologico,
            'dias_desde_siembra': row.dias_desde_siembra,
            'fecha_siembra': row.fecha_siembra,
            'parcela_nombre': row.parcela_nombre,
            'superficie_ha': row.superficie_ha,
            'pendiente_porcentaje': row.pendiente_porcentaje,
            'variedad_nombre': row.variedad_nombre or 'Sin variedad',
            'produccion_potencial_qq_ha': row.produccion_potencial_qq_ha or 70.0,
            'ciclo_vegetativo_dias': row.ciclo_vegetativo_dias or 120,
        }