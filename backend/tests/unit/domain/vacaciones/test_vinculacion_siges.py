import uuid

from src.modules.vacaciones.domain.services.vinculacion_siges import (
    SigesTecnicoInfo,
    nombres_compatibles,
    normalizar_nombre,
    proponer_vinculos,
)


def test_normalizar_nombre_saca_prefijo_cd_acentos_y_mayusculas() -> None:
    assert normalizar_nombre("CD - Agustin HACZEK") == "agustin haczek"
    assert normalizar_nombre("CD - Nicolás MON") == "nicolas mon"


def test_normalizar_nombre_sin_prefijo_no_cambia_de_forma() -> None:
    assert normalizar_nombre("Agustin Haczek") == "agustin haczek"


def test_nombres_compatibles_por_contencion() -> None:
    assert nombres_compatibles("agustin haczek", "agustin haczek jose")
    assert nombres_compatibles("agustin haczek jose", "agustin haczek")


def test_nombres_compatibles_rechaza_nombres_distintos() -> None:
    assert not nombres_compatibles("agustin haczek", "nicolas mon")


def test_nombres_compatibles_rechaza_vacios() -> None:
    assert not nombres_compatibles("", "agustin haczek")


def test_proponer_vinculos_matchea_por_nombre() -> None:
    empleado_id = uuid.uuid4()
    candidatos = [SigesTecnicoInfo(siges_empresa_id=1314, den_comercial="CD - Agustin HACZEK")]

    propuestas = proponer_vinculos([(empleado_id, "Agustin Haczek")], candidatos)

    assert propuestas == {empleado_id: 1314}


def test_proponer_vinculos_no_propone_si_no_hay_candidato() -> None:
    empleado_id = uuid.uuid4()
    candidatos = [SigesTecnicoInfo(siges_empresa_id=1314, den_comercial="CD - Nicolas MON")]

    propuestas = proponer_vinculos([(empleado_id, "Agustin Haczek")], candidatos)

    assert propuestas == {}


def test_proponer_vinculos_descarta_ambiguedad_de_candidato_local() -> None:
    """Dos empleados locales llamados igual (o compatibles) contra el mismo
    técnico de Siges: ninguno de los dos se propone, nunca al azar."""
    ana = uuid.uuid4()
    ana_2 = uuid.uuid4()
    candidatos = [SigesTecnicoInfo(siges_empresa_id=1, den_comercial="CD - Ana Gomez")]

    propuestas = proponer_vinculos([(ana, "Ana Gomez"), (ana_2, "Ana Gomez")], candidatos)

    assert propuestas == {}


def test_proponer_vinculos_descarta_ambiguedad_de_candidato_siges() -> None:
    """Un nombre local compatible con dos técnicos de Siges: se descarta, no
    hay forma de elegir sin ambigüedad."""
    empleado_id = uuid.uuid4()
    candidatos = [
        SigesTecnicoInfo(siges_empresa_id=1, den_comercial="CD - Ana Gomez"),
        SigesTecnicoInfo(siges_empresa_id=2, den_comercial="CD - Ana Gomez Perez"),
    ]

    propuestas = proponer_vinculos([(empleado_id, "Ana Gomez")], candidatos)

    assert propuestas == {}
