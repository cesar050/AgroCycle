"""
CU-FIN-001 — Registrar compra o gasto durante la temporada agrícola.

Permite al agricultor registrar cada inversión realizada:
semillas, fertilizantes, agroquímicos, mano de obra u otros gastos.
Cada compra queda vinculada a la temporada y opcionalmente
a una actividad agronómica específica.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.compra import Compra
from app.domain.repositories.i_compra_repository import ICompraRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarCompraUseCase:
    """
    Implementa CU-FIN-001.

    Responsabilidades:
    1. Verificar que la temporada pertenece al agricultor
    2. Verificar que la temporada está activa
    3. Calcular el costo total desde cantidad y precio unitario
    4. Persistir la compra
    """

    def __init__(
        self,
        db: Session,
        compra_repo: ICompraRepository,
    ):
        self.db = db
        self.compra_repo = compra_repo

    @log_caso_de_uso('CU-FIN-001 Registrar Compra')
    def ejecutar(
        self,
        temporada_id: str,
        agricultor_id: str,
        categoria: str,
        cantidad: float,
        precio_unitario: float,
        fecha_compra: date,
        insumo_id: Optional[int] = None,
        producto_personalizado: Optional[str] = None,
        unidad_medida: Optional[str] = None,
        proveedor: Optional[str] = None,
        actividad_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
    ) -> tuple:
        """
        Registra una compra o gasto en la temporada activa.

        Args:
            temporada_id: UUID de la temporada donde se registra el gasto
            agricultor_id: UUID del usuario autenticado para verificar pertenencia
            categoria: tipo de gasto — semillas, fertilizantes, agroquimicos,
                       mano_obra u otros
            cantidad: cantidad adquirida en la unidad indicada
            precio_unitario: precio por unidad en dólares
            fecha_compra: fecha en que se realizó la compra
            insumo_id: opcional — referencia al catálogo de insumos
            producto_personalizado: nombre si no está en el catálogo
            unidad_medida: kg, litros, sacos, jornales, etc.
            proveedor: nombre del proveedor opcional
            actividad_id: opcional — vincula la compra a una actividad
            usuario_id: UUID del usuario que registra para auditoría

        Returns:
            tuple (dict, int) con el resultado y el código HTTP
        """
        # 1. Verificar que la temporada existe y pertenece al agricultor
        temporada = self._obtener_temporada_del_agricultor(
            temporada_id, agricultor_id
        )

        if not temporada:
            return {
                'error': 'Temporada no encontrada o no pertenece al agricultor'
            }, 404

        # 2. Verificar que la temporada está activa
        if temporada['estado'] != 'activa':
            return {
                'error': f"No se pueden registrar compras en una temporada {temporada['estado']}. "
                         f"Solo se permiten en temporadas activas."
            }, 400

        # 3. Validar que tiene nombre de producto
        if not insumo_id and not producto_personalizado:
            return {
                'error': 'Debe indicar el insumo del catálogo o el nombre del producto personalizado'
            }, 400

        # 4. Calcular costo total
        costo_total = round(cantidad * precio_unitario, 2)

        # 5. Crear entidad — la validación de categoría ocurre en __post_init__
        try:
            compra = Compra(
                temporada_id=temporada_id,
                categoria=categoria,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                costo_total=costo_total,
                fecha_compra=fecha_compra,
                insumo_id=insumo_id,
                producto_personalizado=producto_personalizado,
                unidad_medida=unidad_medida,
                proveedor=proveedor,
                actividad_id=actividad_id,
                registrado_por=usuario_id,
            )
        except ValueError as e:
            return {'error': str(e)}, 400

        # 6. Persistir
        compra_guardada = self.compra_repo.guardar(compra)

        return {
            'id': compra_guardada.id,
            'temporada_id': compra_guardada.temporada_id,
            'categoria': compra_guardada.categoria,
            'cantidad': compra_guardada.cantidad,
            'unidad_medida': compra_guardada.unidad_medida,
            'precio_unitario': compra_guardada.precio_unitario,
            'costo_total': compra_guardada.costo_total,
            'fecha_compra': str(compra_guardada.fecha_compra),
            'proveedor': compra_guardada.proveedor,
            'producto': compra_guardada.producto_personalizado,
            'insumo_id': compra_guardada.insumo_id,
            'actividad_id': compra_guardada.actividad_id,
            'mensaje': 'Compra registrada correctamente',
        }, 201

    def _obtener_temporada_del_agricultor(
        self, temporada_id: str, agricultor_id: str
    ) -> Optional[dict]:
        """
        Verifica que la temporada existe y pertenece al agricultor autenticado.
        Hace un JOIN con agricultores para validar la pertenencia en una sola query.
        """
        row = self.db.execute(
            text("""
                SELECT t.id, t.estado, t.nombre
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
            'estado': row.estado,
            'nombre': row.nombre,
        }