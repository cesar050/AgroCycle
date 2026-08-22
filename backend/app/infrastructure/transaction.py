"""
Gestor de transacciones atómicas para AgroCycle.

Garantiza que si cualquier operación dentro de un bloque falla,
todas las operaciones anteriores se revierten automáticamente.
Evita datos inconsistentes cuando una operación tiene múltiples
pasos en la base de datos.

Ejemplo del problema que resuelve:
    Registrar cosecha:
    Paso 1: guarda produccion_real_qq  ✓
    Paso 2: cierra la temporada        ✗ falla
    Sin transacción: Paso 1 queda guardado, datos inconsistentes
    Con transacción: Paso 1 se revierte automáticamente

Uso:
    with transaccion_atomica(self.db):
        self.db.add(modelo1)
        self.db.add(modelo2)
        # commit automático al salir sin error
        # rollback automático si hay excepción
"""
from contextlib import contextmanager
from sqlalchemy.orm import Session
from app.infrastructure.logging.logger import configurar_logger

logger = configurar_logger('transaccion')


@contextmanager
def transaccion_atomica(db: Session):
    """
    Context manager para transacciones atómicas.

    Hace commit automático si todo sale bien.
    Hace rollback automático si hay cualquier excepción.
    Loguea ambos casos para auditoría.
    """
    try:
        yield db
        db.commit()
        logger.debug('Transaccion completada exitosamente')
    except Exception as e:
        db.rollback()
        logger.error(f'Transaccion revertida: {str(e)}')
        raise