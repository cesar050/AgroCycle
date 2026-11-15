from app.domain.repositories.i_parcela_repository import IParcelaRepository
from app.domain.repositories.i_lote_repository import ILoteRepository
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class GestionarParcelasUseCase:
    """
    CU-GFP-004: Gestionar parcelas.
    Permite al agricultor listar, obtener detalle, editar y eliminar
    las parcelas de sus lotes. La propiedad se verifica subiendo la
    cadena parcela -> lote -> finca -> agricultor.
    """

    def __init__(
        self,
        parcela_repository: IParcelaRepository,
        lote_repository: ILoteRepository,
        finca_repository: IFincaRepository
    ):
        self.parcela_repository = parcela_repository
        self.lote_repository = lote_repository
        self.finca_repository = finca_repository

    def _verificar_propiedad_lote(self, lote_id: str, agricultor_id: str):
        lote = self.lote_repository.buscar_por_id(lote_id)
        if not lote:
            raise ValueError("Lote no encontrado")
        finca = self.finca_repository.buscar_por_id(lote.finca_id)
        if not finca or not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso sobre este lote")
        return lote

    def _verificar_propiedad_parcela(self, parcela_id: str, agricultor_id: str):
        parcela = self.parcela_repository.buscar_por_id(parcela_id)
        if not parcela:
            raise ValueError("Parcela no encontrada")
        self._verificar_propiedad_lote(parcela.lote_id, agricultor_id)
        return parcela

    def _serializar(self, parcela) -> dict:
        return {
            "id": parcela.id,
            "lote_id": parcela.lote_id,
            "nombre": parcela.nombre,
            "superficie_ha": parcela.superficie_ha,
            "tipo_suelo_id": parcela.tipo_suelo_id,
            "pendiente_porcentaje": parcela.pendiente_porcentaje,
            "altitud_promedio_msnm": parcela.altitud_promedio_msnm,
            "altitud_minima_msnm": parcela.altitud_minima_msnm,
            "altitud_maxima_msnm": parcela.altitud_maxima_msnm,
            "orientacion": parcela.orientacion,
            "drenaje": parcela.drenaje,
            "acceso_riego": parcela.acceso_riego,
            "tipo_riego": parcela.tipo_riego,
            "observaciones": parcela.observaciones,
            "tiene_geometria": parcela.tiene_geometria(),
            "activo": parcela.activo,
            "created_at": parcela.created_at.isoformat() if parcela.created_at else None
        }

    @log_caso_de_uso('listar_parcelas')
    def listar(self, lote_id: str, agricultor_id: str) -> list:
        """Lista todas las parcelas activas de un lote del agricultor."""
        self._verificar_propiedad_lote(lote_id, agricultor_id)
        parcelas = self.parcela_repository.listar_por_lote(lote_id)
        return [self._serializar(p) for p in parcelas]

    @log_caso_de_uso('obtener_parcela')
    def obtener(self, parcela_id: str, agricultor_id: str) -> dict:
        """Retorna el detalle completo de una parcela del agricultor."""
        parcela = self._verificar_propiedad_parcela(parcela_id, agricultor_id)
        return self._serializar(parcela)

    @log_caso_de_uso('editar_parcela')
    def editar(self, parcela_id: str, agricultor_id: str, datos: dict) -> dict:
        """
        Edita los atributos agronomicos de una parcela existente.
        Nunca redibuja la geometria ni recalcula topografia — eso solo
        ocurre al registrar una parcela nueva.
        """
        parcela = self._verificar_propiedad_parcela(parcela_id, agricultor_id)

        parcela.nombre = datos.get('nombre', parcela.nombre).strip()
        parcela.tipo_suelo_id = datos.get('tipo_suelo_id', parcela.tipo_suelo_id)
        parcela.drenaje = datos.get('drenaje', parcela.drenaje)
        parcela.acceso_riego = datos.get('acceso_riego', parcela.acceso_riego)
        parcela.tipo_riego = datos.get('tipo_riego', parcela.tipo_riego)
        parcela.observaciones = datos.get('observaciones', parcela.observaciones)

        parcela_actualizada = self.parcela_repository.actualizar(parcela)
        return self._serializar(parcela_actualizada)

    @log_caso_de_uso('eliminar_parcela')
    def eliminar(self, parcela_id: str, agricultor_id: str) -> dict:
        """
        Elimina (soft-delete) una parcela. La parcela es una hoja del
        arbol finca->lote->parcela, nunca tiene hijos que bloqueen el borrado.
        """
        parcela = self._verificar_propiedad_parcela(parcela_id, agricultor_id)
        parcela.activo = False
        parcela_eliminada = self.parcela_repository.actualizar(parcela)

        return {
            "id": parcela_eliminada.id,
            "activo": parcela_eliminada.activo,
            "mensaje": "Parcela eliminada correctamente"
        }
