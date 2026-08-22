from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class GestionarFincasUseCase:
    """
    CU-GFP-001 y CU-GFP-006: Gestionar y visualizar fincas.
    Permite al agricultor listar, obtener detalle y editar sus fincas.
    """

    def __init__(self, finca_repository: IFincaRepository):
        self.finca_repository = finca_repository

    @log_caso_de_uso('listar_fincas')
    def listar(self, agricultor_id: str) -> list:
        """
        Retorna todas las fincas activas del agricultor.
        Solo ve sus propias fincas, nunca las de otros agricultores.
        """
        fincas = self.finca_repository.listar_por_agricultor(agricultor_id)
        return [
            {
                "id": f.id,
                "nombre": f.nombre,
                "ubicacion": f.nombre_completo_ubicacion(),
                "provincia": f.provincia,
                "canton": f.canton,
                "parroquia": f.parroquia,
                "sector": f.sector,
                "descripcion": f.descripcion,
                "superficie_ha": f.superficie_ha,
                "tiene_geometria": f.tiene_geometria(),
                "activo": f.activo,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in fincas
        ]

    @log_caso_de_uso('obtener_finca')
    def obtener(self, finca_id: str, agricultor_id: str) -> dict:
        """
        Retorna el detalle de una finca especifica.
        Verifica que la finca pertenezca al agricultor que la solicita.
        Esto es autorizacion a nivel de dominio usando el metodo
        es_del_agricultor de la entidad Finca.
        """
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca:
            raise ValueError("Finca no encontrada")

        if not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para ver esta finca")

        return {
            "id": finca.id,
            "nombre": finca.nombre,
            "ubicacion": finca.nombre_completo_ubicacion(),
            "provincia": finca.provincia,
            "canton": finca.canton,
            "parroquia": finca.parroquia,
            "sector": finca.sector,
            "descripcion": finca.descripcion,
            "activo": finca.activo,
            "created_at": finca.created_at.isoformat() if finca.created_at else None
        }

    @log_caso_de_uso('editar_finca')
    def editar(self, finca_id: str, agricultor_id: str, datos: dict) -> dict:
        """
        Edita los datos de una finca existente.
        Verifica propiedad antes de permitir la edicion.
        Solo el dueno puede editar su propia finca.
        """
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca:
            raise ValueError("Finca no encontrada")

        if not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para editar esta finca")

        finca.nombre = datos.get('nombre', finca.nombre).strip()
        finca.provincia = datos.get('provincia', finca.provincia)
        finca.canton = datos.get('canton', finca.canton)
        finca.parroquia = datos.get('parroquia', finca.parroquia)
        finca.sector = datos.get('sector', finca.sector)
        finca.descripcion = datos.get('descripcion', finca.descripcion)

        finca_actualizada = self.finca_repository.actualizar(finca)

        return {
            "id": finca_actualizada.id,
            "nombre": finca_actualizada.nombre,
            "ubicacion": finca_actualizada.nombre_completo_ubicacion(),
            "activo": finca_actualizada.activo
        }