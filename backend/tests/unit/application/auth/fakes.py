"""Fakes en memoria de los puertos de auth, para tests de application puros
(sin DB ni argon2 real) — mismo patrón que tests/unit/domain/prestadores/fakes.py."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

from src.modules.auth.domain.entities.password_reset_token import PasswordResetToken
from src.modules.auth.domain.entities.route_visit_count import RouteVisitCount
from src.modules.auth.domain.entities.session import Session
from src.modules.auth.domain.entities.user import User
from src.modules.auth.domain.value_objects.email import Email
from src.modules.auth.domain.value_objects.feature_catalog_entry import FeatureCatalogEntry
from src.modules.auth.domain.value_objects.feature_set import FeatureSet
from src.modules.auth.domain.value_objects.password_hash import PasswordHash
from src.modules.auth.domain.value_objects.permission_set import PermissionSet
from src.modules.auth.domain.value_objects.raw_password import RawPassword
from src.shared.domain.value_objects.feature_key import FeatureKey
from src.shared.domain.value_objects.module_key import ModuleKey
from src.shared.domain.value_objects.permission import Permission


def make_user(
    *,
    email: str = "ana@canaldirecto.com.ar",
    password: str = "Correcta1!",
    is_active: bool = True,
    is_superadmin: bool = False,
    color: str | None = None,
) -> User:
    return User(
        id=uuid.uuid4(),
        email=Email(email),
        password_hash=FakePasswordHasher().hash(RawPassword(password)),
        full_name="Ana Prueba",
        is_active=is_active,
        is_superadmin=is_superadmin,
        created_at=datetime.now(UTC),
        color=color,
    )


def make_session(
    *,
    user_id: uuid.UUID,
    token_hash: bytes = b"h:tok",
    last_seen_delta: timedelta = timedelta(minutes=5),
    expires_delta: timedelta = timedelta(days=7),
    revoked: bool = False,
) -> Session:
    now = datetime.now(UTC)
    return Session(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=token_hash,
        issued_at=now - last_seen_delta,
        expires_at=now + expires_delta,
        last_seen_at=now - last_seen_delta,
        revoked_at=now if revoked else None,
    )


class FakeUserRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, User] = {}
        self.saved: list[User] = []

    async def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.rows.get(user_id)

    async def add(self, user: User) -> None:
        self.rows[user.id] = user

    async def save(self, user: User) -> None:
        self.rows[user.id] = user
        self.saved.append(user)

    async def count_active_superadmins(self) -> int:
        return sum(1 for u in self.rows.values() if u.is_superadmin and u.is_active)


class FakeSessionRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Session] = {}
        self.saved: list[Session] = []
        self.revoked_all: list[tuple[uuid.UUID, uuid.UUID | None]] = []

    async def add(self, session: Session) -> None:
        self.rows[session.id] = session

    async def get_by_token_hash(self, token_hash: bytes) -> Session | None:
        return next((s for s in self.rows.values() if s.token_hash == token_hash), None)

    async def save(self, session: Session) -> None:
        self.rows[session.id] = session
        self.saved.append(session)

    async def revoke_all_for_user(
        self,
        user_id: uuid.UUID,
        *,
        at: datetime,
        except_session_id: uuid.UUID | None = None,
    ) -> None:
        self.revoked_all.append((user_id, except_session_id))
        for session in self.rows.values():
            if session.user_id == user_id and session.id != except_session_id:
                session.revoke(at=at)


class FakePermissionRepository:
    def __init__(self) -> None:
        self.by_user: dict[uuid.UUID, PermissionSet] = {}
        self.replaced: list[tuple[uuid.UUID, PermissionSet, uuid.UUID]] = []

    async def get_for_user(self, user_id: uuid.UUID) -> PermissionSet:
        return self.by_user.get(user_id, PermissionSet(granted=frozenset()))

    async def replace_for_user(
        self, user_id: uuid.UUID, desired: PermissionSet, *, granted_by: uuid.UUID
    ) -> None:
        self.by_user[user_id] = desired
        self.replaced.append((user_id, desired, granted_by))


@dataclass(slots=True)
class RecordedDiff:
    actor_user_id: uuid.UUID
    target_user_id: uuid.UUID
    added: frozenset[Permission]
    removed: frozenset[Permission]


class FakePermissionAuditRepository:
    def __init__(self) -> None:
        self.diffs: list[RecordedDiff] = []
        self.feature_diffs: list[
            tuple[uuid.UUID, uuid.UUID, frozenset[FeatureKey], frozenset[FeatureKey]]
        ] = []

    async def record_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[Permission],
        removed: frozenset[Permission],
    ) -> None:
        self.diffs.append(RecordedDiff(actor_user_id, target_user_id, added, removed))

    async def record_feature_diff(
        self,
        *,
        actor_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
        added: frozenset[FeatureKey],
        removed: frozenset[FeatureKey],
    ) -> None:
        self.feature_diffs.append((actor_user_id, target_user_id, added, removed))


class FakeFeatureGrantRepository:
    def __init__(self) -> None:
        self.by_user: dict[uuid.UUID, FeatureSet] = {}
        self.replaced: list[tuple[uuid.UUID, FeatureSet, uuid.UUID]] = []

    async def get_for_user(self, user_id: uuid.UUID) -> FeatureSet:
        return self.by_user.get(user_id, FeatureSet())

    async def replace_for_user(
        self, user_id: uuid.UUID, features: FeatureSet, *, granted_by: uuid.UUID
    ) -> None:
        self.by_user[user_id] = features
        self.replaced.append((user_id, features, granted_by))


@dataclass(slots=True)
class FakeLoginAttemptRepository:
    """`recent_failures` es la base histórica; además cuenta los fallos que
    se graban durante el test para el email exacto consultado."""

    recent_failures: int = 0
    records: list[tuple[str, str | None, bool]] = field(default_factory=list)
    queried_emails: list[str] = field(default_factory=list)

    async def record(self, *, email: str, ip: str | None, succeeded: bool) -> None:
        self.records.append((email, ip, succeeded))

    async def count_recent_failures(self, *, email: str, since: datetime) -> int:
        self.queried_emails.append(email)
        recorded = sum(1 for e, _, ok in self.records if e == email and not ok)
        return self.recent_failures + recorded


class FakeResetTokenRepository:
    def __init__(self) -> None:
        self.rows: dict[bytes, PasswordResetToken] = {}
        self.marked_used: list[bytes] = []
        self.created: list[tuple[uuid.UUID, datetime]] = []

    async def add(self, token: PasswordResetToken) -> None:
        self.rows[token.token_hash] = token
        self.created.append((token.user_id, datetime.now(UTC)))

    async def count_created_since(self, user_id: uuid.UUID, *, since: datetime) -> int:
        return sum(1 for uid, at in self.created if uid == user_id and at >= since)

    async def get_by_token_hash(self, token_hash: bytes) -> PasswordResetToken | None:
        return self.rows.get(token_hash)

    async def mark_used(self, token_hash: bytes, *, at: datetime) -> None:
        self.marked_used.append(token_hash)
        record = self.rows.get(token_hash)
        if record is not None:
            record.used_at = at


DUMMY_HASH = PasswordHash(value="hash:__dummy__")


class FakePasswordHasher:
    """Hash reversible de juguete: suficiente para verificar el contrato
    hash/verify sin pagar argon2 en cada test. `verified` registra contra
    qué hash se verificó cada candidato."""

    def __init__(self) -> None:
        self.verified: list[PasswordHash] = []

    def hash(self, raw: RawPassword) -> PasswordHash:
        return PasswordHash(value=f"hash:{raw.value}")

    def verify(self, candidate: str, stored: PasswordHash) -> bool:
        self.verified.append(stored)
        return stored.value == f"hash:{candidate}"

    def needs_rehash(self, stored: PasswordHash) -> bool:
        return False

    def dummy_hash(self) -> PasswordHash:
        return DUMMY_HASH


class FakeSessionTokenGenerator:
    def __init__(self, token: str = "tok") -> None:
        self.token = token

    def generate(self) -> str:
        return self.token

    def hash(self, token: str) -> bytes:
        return f"h:{token}".encode()


@dataclass(slots=True)
class SentMail:
    to: str
    subject: str
    body: str


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[SentMail] = []

    async def send(self, *, to: str, subject: str, body: str, html_body: str | None = None) -> None:
        self.sent.append(SentMail(to=to, subject=subject, body=body))


class FakeModuleCatalogRepository:
    """Solo `is_enabled` importa para RecordRouteVisit -- `list_all`/
    `list_actions` no se implementan porque ningún test los ejercita."""

    def __init__(self, enabled: set[str] | None = None) -> None:
        self.enabled = enabled if enabled is not None else {"sla", "insumos", "liquidaciones"}

    async def is_enabled(self, module: ModuleKey) -> bool:
        return module.value in self.enabled


class FakeFeatureCatalogRepository:
    def __init__(self, keys: set[str]) -> None:
        self.entries = [
            FeatureCatalogEntry(
                key=FeatureKey(key),
                module=ModuleKey(key.split("-")[0]),
                label=key,
                description="",
                sort_order=1,
            )
            for key in sorted(keys)
        ]

    async def list_all(self) -> list[FeatureCatalogEntry]:
        return self.entries


@dataclass(slots=True)
class FakeRouteVisitRepository:
    rows: dict[tuple[uuid.UUID, date, str], int] = field(default_factory=dict)
    purged: list[tuple[uuid.UUID, date]] = field(default_factory=list)

    async def increment(
        self, *, user_id: uuid.UUID, route: str, day: date, max_routes_per_day: int
    ) -> None:
        distintas = {r for (u, d, r) in self.rows if u == user_id and d == day}
        if route not in distintas and len(distintas) >= max_routes_per_day:
            return
        key = (user_id, day, route)
        self.rows[key] = self.rows.get(key, 0) + 1

    async def purge_before(self, *, user_id: uuid.UUID, cutoff: date) -> None:
        self.purged.append((user_id, cutoff))
        self.rows = {k: v for k, v in self.rows.items() if not (k[0] == user_id and k[1] < cutoff)}

    async def top_routes(
        self, *, user_id: uuid.UUID, since: date, limit: int
    ) -> list[RouteVisitCount]:
        totals: dict[str, int] = {}
        last: dict[str, date] = {}
        for (u, d, r), count in self.rows.items():
            if u != user_id or d < since:
                continue
            totals[r] = totals.get(r, 0) + count
            last[r] = max(last.get(r, d), d)
        ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
        return [RouteVisitCount(route=r, visits=c, last_visit=last[r]) for r, c in ranked]


class FakeOperadorColorLookup:
    def __init__(self, colors: dict[str, str] | None = None) -> None:
        self.colors = colors or {}

    async def find_color_by_nombre(self, nombre: str) -> str | None:
        return self.colors.get(nombre)
