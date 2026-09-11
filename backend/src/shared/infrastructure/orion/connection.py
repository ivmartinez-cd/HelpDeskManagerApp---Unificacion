"""Connection string de la base Siges del SQL Server ORION (consultas/reportes)
— compartida por todo módulo que consulte Siges: sla, contadores,
liquidaciones, prestadores, preventivos, vacaciones y bono_tecnicos.

Hasta 2026-09-11 esta capa apuntaba a MERCURIO (el motor productivo, con
escrituras); ADR-039 migró el host a ORION para no competir con esas
escrituras, y de paso sacó el prefijo `sla_` histórico de las settings
(`OrionSettings`, config de toda la app, no de un módulo)."""

from src.shared.infrastructure.config.settings import Settings


def build_orion_connection_string(settings: Settings) -> str:
    encrypt = "yes" if settings.orion_encrypt else "no"
    return (
        f"DRIVER={settings.orion_driver};"
        f"SERVER={settings.orion_host};"
        f"DATABASE={settings.orion_database};"
        f"UID={settings.orion_user};"
        f"PWD={settings.orion_password.get_secret_value()};"
        f"Encrypt={encrypt};"
        "TrustServerCertificate=yes"
    )
