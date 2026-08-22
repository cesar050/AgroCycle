"""
CU-FIN-002 — Registrar venta de cosecha.

Cuando el agricultor cosecha y vende, registra:
- Cuántos quintales produjo realmente
- A qué precio vendió cada quintal
- Cuántos vendió y cuántos guardó para autoconsumo
- Los ingresos totales se calculan automáticamente

Este es el caso de uso que cierra el ciclo económico
de la temporada — conecta la producción real con el
módulo financiero para calcular rentabilidad.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso
from app.infrastructure.transaction import transaccion_atomica


class RegistrarVentaUseCase:
    """
    Implementa CU-FIN-002.

    Responsabilidades:
    1. Verificar que la temporada_parcela pertenece al agricultor
    2. Calcular ingresos totales automáticamente
    3. Actualizar producción real y datos de venta
    4. Todo en una sola transacción atómica
    """

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('CU-FIN-002 Registrar Venta de Cosecha')
    def ejecutar(
        self,
        temporada_parcela_id: str,
        agricultor_id: str,
        produccion_real_qq: float,
        fecha_cosecha: date,
        precio_venta_qq: float,
        volumen_vendido_qq: float,
        produccion_autoconsumo_qq: Optional[float] = None,
    ) -> tuple:
        """
        Registra la venta de cosecha de una parcela.

        Args:
            temporada_parcela_id: UUID de la temporada_parcela
            agricultor_id: UUID del usuario autenticado
            produccion_real_qq: quintales totales cosechados
            fecha_cosecha: fecha en que se realizó la cosecha
            precio_venta_qq: precio por quintal en USD
            volumen_vendido_qq: quintales efectivamente vendidos
            produccion_autoconsumo_qq: quintales para consumo propio

        Returns:
            tuple (dict resultado, int código HTTP)
        """
        # 1. Verificar pertenencia
        tp_data = self._obtener_temporada_parcela(
            temporada_parcela_id, agricultor_id
        )

        if not tp_data:
            return {
                'error': 'Temporada de parcela no encontrada '
                         'o no pertenece al agricultor'
            }, 404

        # 2. Verificar que la temporada está activa
        if tp_data['temporada_estado'] != 'activa':
            return {
                'error': f"No se puede registrar venta en una temporada "
                         f"{tp_data['temporada_estado']}."
            }, 400

        # 3. Validar que los quintales vendidos no superen los producidos
        if volumen_vendido_qq > produccion_real_qq:
            return {
                'error': f"El volumen vendido ({volumen_vendido_qq} qq) no puede "
                         f"superar la producción real ({produccion_real_qq} qq)."
            }, 400

        # 4. Calcular autoconsumo si no se proporcionó
        if produccion_autoconsumo_qq is None:
            produccion_autoconsumo_qq = round(
                produccion_real_qq - volumen_vendido_qq, 2
            )

        # 5. Calcular ingresos totales automáticamente
        ingresos_totales = round(volumen_vendido_qq * precio_venta_qq, 2)

        # 6. Guardar en transacción atómica
        try:
            with transaccion_atomica(self.db):
                self.db.execute(
                    text("""
                        UPDATE temporada_parcelas
                        SET
                            produccion_real_qq       = :produccion_real_qq,
                            fecha_cosecha            = :fecha_cosecha,
                            precio_venta_qq          = :precio_venta_qq,
                            volumen_vendido_qq       = :volumen_vendido_qq,
                            ingresos_totales         = :ingresos_totales,
                            produccion_autoconsumo_qq = :autoconsumo,
                            updated_at               = NOW()
                        WHERE id = CAST(:tp_id AS uuid)
                    """),
                    {
                        'produccion_real_qq': produccion_real_qq,
                        'fecha_cosecha': fecha_cosecha,
                        'precio_venta_qq': precio_venta_qq,
                        'volumen_vendido_qq': volumen_vendido_qq,
                        'ingresos_totales': ingresos_totales,
                        'autoconsumo': produccion_autoconsumo_qq,
                        'tp_id': temporada_parcela_id,
                    }
                )
        except Exception as e:
            return {
                'error': f'Error al registrar la venta: {str(e)}'
            }, 500

        # 7. Calcular precio por quintal producido
        costo_estimado_qq = None
        if tp_data['superficie_ha'] and produccion_real_qq > 0:
            rendimiento_qq_ha = round(
                produccion_real_qq / float(tp_data['superficie_ha']), 2
            )
        else:
            rendimiento_qq_ha = None

        return {
            'temporada_parcela_id': temporada_parcela_id,
            'parcela_nombre': tp_data['parcela_nombre'],
            'venta': {
                'produccion_real_qq': produccion_real_qq,
                'fecha_cosecha': str(fecha_cosecha),
                'precio_venta_qq': precio_venta_qq,
                'volumen_vendido_qq': volumen_vendido_qq,
                'produccion_autoconsumo_qq': produccion_autoconsumo_qq,
                'ingresos_totales': ingresos_totales,
            },
            'indicadores': {
                'rendimiento_qq_ha': rendimiento_qq_ha,
                'ingreso_por_ha': round(
                    ingresos_totales / float(tp_data['superficie_ha']), 2
                ) if tp_data['superficie_ha'] else None,
            },
            'mensaje': (
                f"Venta registrada. Ingresos totales: "
                f"${ingresos_totales:.2f} USD por "
                f"{volumen_vendido_qq} quintales vendidos."
            ),
        }, 200

    def _obtener_temporada_parcela(
        self, temporada_parcela_id: str, agricultor_id: str
    ) -> Optional[dict]:
        """
        Verifica pertenencia y obtiene datos necesarios
        en una sola query eficiente.
        """
        row = self.db.execute(
            text("""
                SELECT
                    tp.id,
                    tp.produccion_real_qq,
                    p.nombre        AS parcela_nombre,
                    p.superficie_ha,
                    t.estado        AS temporada_estado,
                    t.nombre        AS temporada_nombre
                FROM temporada_parcelas tp
                JOIN parcelas p      ON tp.parcela_id = p.id
                JOIN temporadas t    ON tp.temporada_id = t.id
                JOIN agricultores a  ON t.agricultor_id = a.id
                WHERE tp.id = CAST(:tp_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'tp_id': temporada_parcela_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'parcela_nombre': row.parcela_nombre,
            'superficie_ha': row.superficie_ha,
            'temporada_estado': row.temporada_estado,
            'temporada_nombre': row.temporada_nombre,
            'produccion_previa': row.produccion_real_qq,
        }