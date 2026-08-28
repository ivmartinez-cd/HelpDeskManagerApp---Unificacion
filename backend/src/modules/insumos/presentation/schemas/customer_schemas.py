"""Schemas de presentación del módulo Clientes."""

from pydantic import BaseModel

from src.modules.insumos.domain.value_objects.zone_contacts import (
    Customer,
    SdsContactRow,
    ZoneContactPreviewRow,
    ZoneContactRow,
)


class OkResponse(BaseModel):
    ok: bool = True


class CustomerOut(BaseModel):
    customer_id: int
    name: str
    enabled: bool
    has_contacts: bool
    client_mail_enabled: bool

    @classmethod
    def from_domain(cls, c: Customer) -> "CustomerOut":
        return cls(
            customer_id=c.customer_id,
            name=c.name,
            enabled=c.enabled,
            has_contacts=c.has_contacts,
            client_mail_enabled=c.client_mail_enabled,
        )


class CustomerPatchBody(BaseModel):
    """None = no tocar ese campo. `enabled` (monitoreo) y `client_mail_enabled` (aviso
    por mail al cliente) son toggles independientes — un PATCH que solo manda uno de
    los dos no debe pisar el otro."""

    enabled: bool | None = None
    client_mail_enabled: bool | None = None


class BulkToggleBody(BaseModel):
    enabled: bool = False


class SyncCustomersResponse(BaseModel):
    ok: bool
    count: int


class ZoneContactOut(BaseModel):
    zone: str
    sol_apellido: str
    sol_nombre: str
    sol_telefono: str
    sol_email: str
    sol_sector: str
    dest_apellido: str
    dest_nombre: str
    dest_telefono: str
    dest_email: str
    dest_sector: str
    observaciones: str

    @classmethod
    def from_domain(cls, r: ZoneContactRow) -> "ZoneContactOut":
        return cls(**r.__dict__)


class ZoneContactBody(BaseModel):
    zone: str = ""
    sol_apellido: str = ""
    sol_nombre: str = ""
    sol_telefono: str = ""
    sol_email: str = ""
    sol_sector: str = ""
    dest_apellido: str = ""
    dest_nombre: str = ""
    dest_telefono: str = ""
    dest_email: str = ""
    dest_sector: str = ""
    observaciones: str = ""

    def to_domain_row(self) -> ZoneContactRow:
        return ZoneContactRow(**self.model_dump())


class SeedDefaultContactsBody(BaseModel):
    customer_ids: list[int]
    zone: str = ""
    sol_apellido: str = ""
    sol_nombre: str = ""
    sol_telefono: str = ""
    sol_email: str = ""
    sol_sector: str = ""
    dest_apellido: str = ""
    dest_nombre: str = ""
    dest_telefono: str = ""
    dest_email: str = ""
    dest_sector: str = ""
    observaciones: str = ""

    def to_domain_row(self) -> ZoneContactRow:
        data = self.model_dump()
        data.pop("customer_ids")
        return ZoneContactRow(**data)


class SeedResponse(BaseModel):
    ok: bool
    updated: int


class ImportFromSupplyBody(BaseModel):
    supply_id: str

    def parsed_supply_id(self) -> int | None:
        try:
            return int(self.supply_id.strip().split("-")[0])
        except (ValueError, AttributeError):
            return None


class ImportContactsResponse(BaseModel):
    ok: bool
    zone: str | None = None
    row: ZoneContactOut | None = None
    error: str | None = None


class SdsContactOut(BaseModel):
    zone: str
    contacto: str
    email: str
    sucursal: str

    @classmethod
    def from_domain(cls, r: SdsContactRow) -> "SdsContactOut":
        return cls(zone=r.zone, contacto=r.contacto, email=r.email, sucursal=r.sucursal)


class ZoneContactPreviewRowOut(BaseModel):
    zone: str
    apellido: str
    nombre: str
    email: str
    telefono: str
    already_configured: bool
    error: str | None
    current_apellido: str
    current_nombre: str
    current_email: str
    current_telefono: str

    @classmethod
    def from_domain(cls, r: ZoneContactPreviewRow) -> "ZoneContactPreviewRowOut":
        return cls(
            zone=r.zone,
            apellido=r.apellido,
            nombre=r.nombre,
            email=r.email,
            telefono=r.telefono,
            already_configured=r.already_configured,
            error=r.error,
            current_apellido=r.current_apellido,
            current_nombre=r.current_nombre,
            current_email=r.current_email,
            current_telefono=r.current_telefono,
        )


class ZoneContactPreviewResponse(BaseModel):
    ok: bool
    rows: list[ZoneContactPreviewRowOut] = []
    error: str | None = None


class ZoneContactApplyRowIn(BaseModel):
    zone: str
    overwrite: bool = False


class ZoneContactApplyBody(BaseModel):
    rows: list[ZoneContactApplyRowIn]


class ZoneContactApplyResponse(BaseModel):
    ok: bool
    applied: int = 0
    error: str | None = None
