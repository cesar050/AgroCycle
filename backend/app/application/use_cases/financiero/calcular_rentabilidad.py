"""
CU-FIN-004 — Calcular rentabilidad de una temporada agrícola.

Consolida todos los gastos registrados, los ingresos por venta
de cosecha y calcula la ganancia o pérdida neta de la temporada.
También calcula el costo por quintal producido — el indicador
más importante para que el agricultor sepa si le conviene seguir
cultivando o necesita ajustar su manejo.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.resultado_financiero import ResultadoFinanciero
from app.domain.repositories.i_compra_repository import ICompraRepository
from app.domain.repositories.i_resultado_financiero_repository import IResultadoFinancieroRepository
from app.infrastructure.transaction import transaccion_atomica
from app.infrastructure.logging.logger import log_caso_de_uso


class CalcularRentabilidadUseCase:
    """
    Implementa CU-FIN-004.

    Responsabilidades:
    1. Sumar todos los gastos por categoría
    2. Obtener ingresos totales de la venta de cosecha
    3. Calcular ganancia neta y margen de rentabilidad
    4. Calcular costo por quintal producido
    5. Persistir el resultado para consultas futuras
    """

    def __init__(
        self,
        db: Session,
        compra_repo: ICompraRepository,
        resultado_repo: IResultadoFinancieroRepository,
    ):
        self.db = db
        self.compra_repo = compra_repo
        self.resultado_repo = resultado_repo

    @log_caso_de_uso('CU-FIN-004 Calcular Rentabilidad')
    def ejecutar(
        self,
        temporada_id: str,
        agricultor_id: str,
    ) -> tuple:
        """
        Calcula y persiste la rentabilidad de una temporada.

        Puede llamarse en cualquier momento de la temporada para
        ver la situación financiera actual. Si la temporada está
        cerrada con producción real, calcula el costo por quintal.

        Args:
            temporada_id: UUID de la temporada a calcular
            agricultor_id: UUID del usuario para verificar pertenencia

        Returns:
            tuple (dict, int) con resultado financiero y código HTTP
        """
        # 1. Verificar que la temporada existe y pertenece al agricultor
        temporada = self._obtener_temporada(temporada_id, agricultor_id)

        if not temporada:
            return {
                'error': 'Temporada no encontrada o no pertenece al agricultor'
            }, 404

        # 2. Obtener totales de gasto por categoría desde BD
        totales_gasto = self.compra_repo.total_por_categoria(temporada_id)

        # 3. Obtener ingresos y producción real de las ventas
        datos_venta = self._obtener_datos_venta(temporada_id)

        # 4. Construir entidad de resultado financiero
        resultado = ResultadoFinanciero(
            temporada_id=temporada_id,
            ingresos_totales=datos_venta['ingresos_totales'],
            costos_totales=totales_gasto['total'],
            costo_semillas=totales_gasto['semillas'],
            costo_fertilizantes=totales_gasto['fertilizantes'],
            costo_agroquimicos=totales_gasto['agroquimicos'],
            costo_mano_obra=totales_gasto['mano_obra'],
            costo_otros=totales_gasto['otros'],
            precio_venta_promedio_qq=datos_venta['precio_promedio_qq'],
        )

        # 5. Calcular ganancia, margen y costo por quintal
        resultado.calcular(
            produccion_qq=datos_venta['produccion_total_qq']
        )

        # 6. Persistir — upsert para no duplicar si ya existe
        try:
            with transaccion_atomica(self.db):
                resultado_guardado = self.resultado_repo.guardar(resultado)
        except Exception as e:
            return {
                'error': 'Error al calcular la rentabilidad. Intenta de nuevo.'
            }, 500

        return self._construir_respuesta(
            resultado_guardado, temporada, totales_gasto, datos_venta
        ), 200

    def _obtener_temporada(
        self, temporada_id: str, agricultor_id: str
    ) -> Optional[dict]:
        """
        Obtiene datos básicos de la temporada verificando pertenencia.
        """
        row = self.db.execute(
            text("""
                SELECT t.id, t.nombre, t.estado, t.fecha_inicio
                FROM temporadas t
                JOIN agricultores a ON t.agricultor_id = a.id
                WHERE t.id = CAST(:temporada_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'temporada_id': temporada_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': row.nombre,
            'estado': row.estado,
            'fecha_inicio': str(row.fecha_inicio),
        }

    def _obtener_datos_venta(self, temporada_id: str) -> dict:
        """
        Obtiene ingresos totales y producción real desde temporada_parcelas.
        Si la temporada no está cerrada, los ingresos son 0 —
        el agricultor aún no ha vendido.
        """
        row = self.db.execute(
            text("""
                SELECT
                    COALESCE(SUM(tp.ingresos_totales), 0)      AS ingresos_totales,
                    COALESCE(SUM(tp.produccion_real_qq), 0)    AS produccion_total_qq,
                    CASE
                        WHEN SUM(tp.produccion_real_qq) > 0
                        THEN SUM(tp.ingresos_totales) / SUM(tp.produccion_real_qq)
                        ELSE 0
                    END                                         AS precio_promedio_qq
                FROM temporada_parcelas tp
                WHERE tp.temporada_id = CAST(:temporada_id AS uuid)
                  AND tp.activo = true
            """),
            {'temporada_id': temporada_id}
        ).fetchone()

        return {
            'ingresos_totales': float(row.ingresos_totales or 0),
            'produccion_total_qq': float(row.produccion_total_qq or 0) or None,
            'precio_promedio_qq': float(row.precio_promedio_qq or 0) or None,
        }

    def _construir_respuesta(
        self,
        resultado: ResultadoFinanciero,
        temporada: dict,
        totales_gasto: dict,
        datos_venta: dict,
    ) -> dict:
        """
        Construye la respuesta final para el agricultor.
        Organiza la información de forma clara y comprensible.
        """
        return {
            'temporada': {
                'id': temporada['id'],
                'nombre': temporada['nombre'],
                'estado': temporada['estado'],
            },
            'gastos': {
                'semillas': totales_gasto['semillas'],
                'fertilizantes': totales_gasto['fertilizantes'],
                'agroquimicos': totales_gasto['agroquimicos'],
                'mano_obra': totales_gasto['mano_obra'],
                'otros': totales_gasto['otros'],
                'total': totales_gasto['total'],
            },
            'ingresos': {
                'total': resultado.ingresos_totales,
                'produccion_qq': datos_venta['produccion_total_qq'],
                'precio_promedio_qq': datos_venta['precio_promedio_qq'],
            },
            'resultado': {
                'ganancia_neta': resultado.ganancia_neta,
                'margen_rentabilidad_porcentaje': resultado.margen_rentabilidad_porcentaje,
                'costo_por_quintal': resultado.costo_por_quintal,
                'interpretacion': resultado.resumen_texto(),
                'hay_perdida': resultado.hay_perdida(),
            },
        }