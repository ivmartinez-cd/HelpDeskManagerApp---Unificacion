"""Puerto de lectura de la bitácora de liquidaciones de Web Agentes
(`dbo.Bitacora` de Siges, Tipo='Liquidation', Origen='webagentes') y puerto
del aviso en la campanita cuando comenta un PST.

Solo lectura contra Siges: la bitácora la escribe Web Agentes (legacy), acá
solo se detectan los comentarios nuevos de prestadores."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ComentarioBitacora:
    """Un comentario de un PST. `numero_liquidacion_cd` es el número de CD sin
    dígito verificador (3984), localmente se guarda con dígito (3984-4).
    `prestador` es la `Den_Comercial` de la empresa del usuario, o None si el
    usuario no está en `UsuariosWeb` (Web Agentes graba 'Anonimo')."""

    id_consulta: int
    numero_liquidacion_cd: int
    fecha: datetime
    usuario: str
    prestador: str | None
    texto: str


@dataclass(frozen=True, slots=True)
class AvisoComentario:
    """Comentario + la liquidación local a la que lleva el aviso (None si
    todavía no se sincronizó a HDM)."""

    comentario: ComentarioBitacora
    liquidacion_id: UUID | None
    numero_liquidacion: str | None


@dataclass(frozen=True, slots=True)
class EntradaBitacora:
    """Un comentario del hilo de una liquidación, de PST o de Canal Directo.
    `autor` es el nombre para mostrar: nombre y apellido del usuario de Canal,
    o la `Den_Comercial` de la empresa del PST; None si no se puede resolver."""

    id_consulta: int
    fecha: datetime
    usuario: str
    autor: str | None
    es_canal: bool
    texto: str


class BitacoraGateway(Protocol):
    async def comentarios_pst_recientes(self, horas: int) -> list[ComentarioBitacora]:
        """Comentarios de PST (no de usuarios de Canal Directo) de las últimas
        `horas`, en orden de carga."""
        ...

    async def hilo_de_liquidacion(self, numero_liquidacion_cd: int) -> list[EntradaBitacora]:
        """Todos los comentarios de una liquidación (número de CD sin dígito
        verificador), en orden de carga."""
        ...


class AvisadorComentariosBitacora(Protocol):
    async def avisar(self, avisos: list[AvisoComentario]) -> None:
        """Idempotente por comentario: publicar dos veces el mismo no duplica."""
        ...
