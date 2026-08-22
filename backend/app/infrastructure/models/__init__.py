"""
Registro central de todos los modeos ORM de AgroCycle
Los modelos deben importarse en orden de dependencia:
primero las tablas padre, luego las que dependan de ellas.
SQLALchemy necesita conocer todos los modelos antes de resolver
los foreign keys entre tablas.
Si agregas un modelo nuevo al sistema, agregalo aqui en el orden correcto 
"""

from app.infrastructure.models import rol_model
from app.infrastructure.models import usuario_model
from app.infrastructure.models import agricultor_model
from app.infrastructure.models import agronomo_model
from app.infrastructure.models import finca_model
from app.infrastructure.models import lote_model
from app.infrastructure.models import parcela_model
from app.infrastructure.models import tipo_suelo_model
from app.infrastructure.models import cultivo_model
from app.infrastructure.models import variedad_semilla_model
from app.infrastructure.models import temporada_model
from app.infrastructure.models import temporada_parcela_model
from app.infrastructure.models import indicador_estres_model
from app.infrastructure.models import estimacion_model
from app.infrastructure.models import dato_climatico_model
from app.infrastructure.models import tipo_actividad_model
from app.infrastructure.models import actividad_model
from app.infrastructure.models import compra_model
from app.infrastructure.models import resultado_financiero_model
from app.infrastructure.models import observacion_tecnica_model
from app.infrastructure.models import recomendacion_agronomica_model
from app.infrastructure.models import evaluacion_campo_model
from app.infrastructure.models import riego_model
from app.infrastructure.models import fertilizacion_model
from app.infrastructure.models import control_fitosanitario_model
from app.infrastructure.models import mano_obra_model
