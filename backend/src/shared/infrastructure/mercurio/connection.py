"""Connection string de la base Siges del SQL Server MERCURIO — compartida
por todo módulo que consulte esa base (hoy sla y prestadores). Las settings
siguen viviendo bajo el nombre histórico `sla_mercurio_*` (fueron las
primeras en usarlas) pero son la config de MERCURIO para toda la app, no
algo privado de sla — no se renombraron para no tocar un integración ya
verificada en producción."""

from src.shared.infrastructure.config.settings import Settings


def build_mercurio_connection_string(settings: Settings) -> str:
    encrypt = "yes" if settings.sla_mercurio_encrypt else "no"
    return (
        f"DRIVER={settings.sla_mercurio_driver};"
        f"SERVER={settings.sla_mercurio_host};"
        f"DATABASE={settings.sla_mercurio_database};"
        f"UID={settings.sla_mercurio_user};"
        f"PWD={settings.sla_mercurio_password.get_secret_value()};"
        f"Encrypt={encrypt};"
        "TrustServerCertificate=yes"
    )
