"""
Sistema de logs estructurado para AgroCycle.
Usa el Decorator Pattern para registrar automaticamente
las acciones de los casos de uso sin contaminar la logica de negocio.
"""
import logging
from functools import wraps


def configurar_logger(nombre: str) -> logging.Logger:
    """
    Crea y configura un logger con formato legible.
    Cada modulo del sistema tiene su propio logger identificado por nombre.
    """
    logger = logging.getLogger(nombre)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_caso_de_uso(nombre_accion: str):
    """
    Decorator Pattern aplicado al logging.
    Envuelve cualquier metodo de caso de uso y registra:
    - INICIO de la accion
    - EXITO si termina bien
    - WARNING si es un error de negocio esperado (ValueError)
    - ERROR si es un fallo inesperado del sistema
    """
    def decorador(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            logger = configurar_logger(self.__class__.__name__)
            logger.info(f"INICIO | accion={nombre_accion}")
            try:
                resultado = func(self, *args, **kwargs)
                logger.info(f"EXITO | accion={nombre_accion}")
                return resultado
            except ValueError as e:
                logger.warning(f"ADVERTENCIA | accion={nombre_accion} | motivo={str(e)}")
                raise
            except Exception as e:
                logger.error(f"ERROR CRITICO | accion={nombre_accion} | error={str(e)}")
                raise
        return wrapper
    return decorador


logger_sistema = configurar_logger('agrocycle')
