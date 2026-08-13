"""Tests de ImportarPrestadorMaestro — orquestación (resolver/crear Prestador,
SPSTs, Tarifarios y Tabla KM a partir de un `ResultadoImportacionMaestro` fijo). La
lógica de parseo del Excel ya está cubierta por
`test_importacion_maestro_parsing.py`; acá solo se verifica que el caso de uso
conecta las piezas y, sobre todo, que el dedup contra la base funciona (el
hallazgo más grave de la revisión de diseño: sin él, re-importar el mismo archivo
duplicaba tarifarios en cada corrida)."""

from datetime import date

from src.modules.liquidaciones.application.dtos.importar_prestador_maestro import (
    ImportarPrestadorMaestroResultado,
)
from src.modules.liquidaciones.application.use_cases.importar_prestador_maestro import (
    ImportarPrestadorMaestro,
    ImportarPrestadorMaestroPorts,
)
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    ResultadoImportacionMaestro,
    SpstImportado,
    TablaKmImportada,
    TarifarioImportado,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_tarifario
from tests.unit.domain.liquidaciones.fakes import (
    FakePrestadorRepository,
    FakeSpstRepository,
    FakeTablaKmRepository,
)
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTarifarioRepository
from tests.unit.domain.liquidaciones.fakes_maestro import FakePrestadorMaestroFileParser

ARCHIVO_NOMBRE = "PENTACOM 202601.xlsx"
ARCHIVO_CONTENIDO = b"<contenido-fake>"


def make_resultado_maestro(**overrides: object) -> ResultadoImportacionMaestro:
    defaults: dict[str, object] = {
        "nombre_corto": "PENTACOM",
        "vigencia": date(2026, 1, 1),
        "hoja_tabla_km": "TABLA KMS",
        "spsts": [SpstImportado(nombre="BASE NORTE")],
        "tarifarios": [
            TarifarioImportado(
                tipo_servicio="correctivo",
                costo_servicio=1500.0,
                costo_km=100.0,
                vigencia_desde=date(2026, 1, 1),
            )
        ],
        "tabla_km": [
            TablaKmImportada(
                empresa_nombre="EMPRESA A",
                sucursal_nombre="SUC A",
                domicilio_cliente=None,
                localidad_cliente=None,
                provincia_cliente=None,
                kms_recorrido=45.0,
                aplica_viatico=True,
                kms_a_facturar=45.0,
                umbral_viatico=30.0,
                url_maps=None,
                spst_nombre="BASE NORTE",
            )
        ],
    }
    defaults.update(overrides)
    return ResultadoImportacionMaestro(**defaults)  # type: ignore[arg-type]


class World:
    def __init__(self, resultado: ResultadoImportacionMaestro | None = None) -> None:
        self.prestadores = FakePrestadorRepository()
        self.spsts = FakeSpstRepository()
        self.tarifarios = FakeConfigTarifarioRepository()
        self.tabla_km = FakeTablaKmRepository()
        self.parser = FakePrestadorMaestroFileParser(resultado or make_resultado_maestro())
        self.use_case = ImportarPrestadorMaestro(
            ImportarPrestadorMaestroPorts(
                parser=self.parser,
                prestadores=self.prestadores,
                spsts=self.spsts,
                tarifarios=self.tarifarios,
                tabla_km=self.tabla_km,
            )
        )

    async def importar(self) -> ImportarPrestadorMaestroResultado:
        return await self.use_case.execute(
            contenido=ARCHIVO_CONTENIDO, nombre_archivo=ARCHIVO_NOMBRE
        )


async def test_prestador_inexistente_se_crea() -> None:
    world = World()

    resultado = await world.importar()

    assert resultado.prestador_creado is True
    creado = world.prestadores.rows[resultado.prestador_id]
    assert creado.nombre_corto == "PENTACOM"


async def test_prestador_existente_con_distinta_capitalizacion_no_duplica() -> None:
    prestador = make_prestador(nombre_corto="PENTACOM")
    world = World(resultado=make_resultado_maestro(nombre_corto="Pentacom"))
    world.prestadores.rows[prestador.id] = prestador

    resultado = await world.importar()

    assert resultado.prestador_creado is False
    assert resultado.prestador_id == prestador.id
    assert len(world.prestadores.rows) == 1


async def test_spst_nuevo_se_crea_y_se_matchea_en_tabla_km() -> None:
    world = World()

    resultado = await world.importar()

    assert resultado.spsts_creados == 1
    entrada = world.tabla_km.rows[0]
    spst_creado = next(iter(world.spsts.rows))
    assert entrada.spst_id == spst_creado.id


async def test_reimportar_el_mismo_archivo_no_duplica_tarifarios() -> None:
    """Fix del hallazgo más grave de la revisión de diseño: el borrador original
    solo dedupeaba tarifarios en memoria contra el archivo, nunca contra la base —
    re-importar el mismo mes creaba un tarifario duplicado en cada corrida."""
    world = World()

    primera = await world.importar()
    segunda = await world.importar()

    assert primera.tarifarios_creados == 1
    assert segunda.tarifarios_creados == 0
    assert segunda.tarifarios_omitidos == 1
    assert len(world.tarifarios.rows) == 1


async def test_tarifario_con_vigencia_distinta_no_se_considera_duplicado() -> None:
    world = World()
    prestador = await world.prestadores.create(
        nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None
    )
    world.tarifarios.rows = [
        make_tarifario(
            prestador_id=prestador.id,
            tipo_servicio="correctivo",
            costo_servicio=1500.0,
            vigencia_desde=date(2025, 12, 1),
        )
    ]

    resultado = await world.importar()

    assert resultado.tarifarios_creados == 1
    assert resultado.tarifarios_omitidos == 0


async def test_importar_recadena_vigencias_dentro_del_grupo() -> None:
    """Dos vigencias del mismo tipo en el archivo: la más vieja se cierra el día
    anterior a la más nueva; la última queda abierta (divergencia consciente vs. el
    legacy, que dejaba las dos abiertas/solapadas)."""
    world = World(
        resultado=make_resultado_maestro(
            tarifarios=[
                TarifarioImportado(
                    tipo_servicio="correctivo",
                    costo_servicio=1500.0,
                    costo_km=100.0,
                    vigencia_desde=date(2026, 1, 1),
                ),
                TarifarioImportado(
                    tipo_servicio="correctivo",
                    costo_servicio=1800.0,
                    costo_km=120.0,
                    vigencia_desde=date(2026, 6, 1),
                ),
            ]
        )
    )

    await world.importar()

    por_desde = {t.vigencia_desde: t for t in world.tarifarios.rows}
    assert por_desde[date(2026, 1, 1)].vigencia_hasta == date(2026, 5, 31)
    assert por_desde[date(2026, 6, 1)].vigencia_hasta is None


async def test_importar_recadena_contra_tarifario_preexistente() -> None:
    """El tarifario ya persistido del mismo grupo (tipo, zona=None) se cierra contra
    el recién importado."""
    world = World()
    prestador = await world.prestadores.create(
        nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None
    )
    previo = make_tarifario(
        prestador_id=prestador.id,
        tipo_servicio="correctivo",
        costo_servicio=1200.0,
        vigencia_desde=date(2025, 6, 1),
        vigencia_hasta=None,
    )
    world.tarifarios.rows = [previo]

    await world.importar()  # trae "correctivo" con vigencia_desde 2026-01-01

    cerrado = await world.tarifarios.get_by_id(previo.id)
    assert cerrado is not None
    assert cerrado.vigencia_hasta == date(2025, 12, 31)


async def test_importar_sin_tarifarios_nuevos_no_recadena() -> None:
    """Si todos los tarifarios del archivo se omiten por duplicados, no se toca
    ninguna vigencia ya persistida — aunque el grupo tenga solapes preexistentes."""
    world = World()
    prestador = await world.prestadores.create(
        nombre="PENTACOM", nombre_corto="PENTACOM", cuit=None, region=None
    )
    solapado = make_tarifario(
        prestador_id=prestador.id,
        tipo_servicio="correctivo",
        costo_servicio=1200.0,
        vigencia_desde=date(2025, 6, 1),
        vigencia_hasta=None,
    )
    duplicado_del_archivo = make_tarifario(
        prestador_id=prestador.id,
        tipo_servicio="correctivo",
        costo_servicio=1500.0,
        vigencia_desde=date(2026, 1, 1),
        vigencia_hasta=None,
    )
    world.tarifarios.rows = [solapado, duplicado_del_archivo]

    resultado = await world.importar()

    assert resultado.tarifarios_creados == 0
    intacto = await world.tarifarios.get_by_id(solapado.id)
    assert intacto is not None
    assert intacto.vigencia_hasta is None


async def test_tabla_km_ya_existente_se_omite() -> None:
    world = World()
    await world.importar()

    segunda = await world.importar()

    assert segunda.tabla_km_creadas == 0
    assert segunda.tabla_km_omitidas == 1
    assert len(world.tabla_km.rows) == 1


async def test_hoja_tabla_km_ausente_se_refleja_en_el_resultado() -> None:
    world = World(
        resultado=make_resultado_maestro(hoja_tabla_km=None, spsts=[], tabla_km=[])
    )

    resultado = await world.importar()

    assert resultado.hoja_tabla_km is None
    assert resultado.tabla_km_creadas == 0


async def test_parser_recibe_contenido_y_nombre_de_archivo() -> None:
    world = World()

    await world.importar()

    assert len(world.parser.calls) == 1
    contenido_recibido, nombre_recibido = world.parser.calls[0]
    assert contenido_recibido == ARCHIVO_CONTENIDO
    assert nombre_recibido == ARCHIVO_NOMBRE
