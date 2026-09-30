from src.modules.notificaciones.domain.value_objects.audiencia import (
    audiencia_funcion,
    audiencia_permiso,
    audiencias_de,
)
from src.shared.domain.value_objects.action_key import ActionKey
from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission


def test_las_audiencias_de_un_usuario_coinciden_con_las_que_publican_los_modulos() -> None:
    mias = audiencias_de(frozenset({"sla-avisos-mesa-ayuda"}), frozenset({("sla", "view")}))
    assert audiencia_funcion(FeatureKey("sla-avisos-mesa-ayuda")) in mias
    assert audiencia_permiso(Permission(ModuleKey("sla"), ActionKey("view"))) in mias
    assert audiencia_permiso(Permission(ModuleKey("sla"), ActionKey("update"))) not in mias


def test_sin_funciones_ni_permisos_no_pertenece_a_ninguna_audiencia() -> None:
    assert audiencias_de(frozenset(), frozenset()) == frozenset()
