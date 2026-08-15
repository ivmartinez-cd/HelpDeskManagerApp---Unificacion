"""Importa los modelos ORM de todos los módulos para que se registren en
Base.metadata antes de correr Alembic autogenerate o cualquier DDL. Un módulo
nuevo se suma acá cuando llegue (import con efecto secundario, sin uso directo).
"""

from src.modules.analisis_log_hp.infrastructure import models as _pi_models  # noqa: F401
from src.modules.auth.infrastructure import models as _auth_models  # noqa: F401
from src.modules.contadores.infrastructure import models as _contadores_models  # noqa: F401
from src.modules.insumos.infrastructure import models as _insumos_models  # noqa: F401
from src.modules.prestadores.infrastructure import models as _prestadores_models  # noqa: F401
from src.modules.preventivos.infrastructure import models as _preventivos_models  # noqa: F401
from src.modules.sla.infrastructure import models as _sla_models  # noqa: F401
from src.modules.turnos.infrastructure import models as _turnos_models  # noqa: F401
from src.modules.vacaciones.infrastructure import models as _vacaciones_models  # noqa: F401
