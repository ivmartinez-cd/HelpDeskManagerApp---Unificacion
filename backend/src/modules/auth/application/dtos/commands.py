from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: str
    password: str
    ip: str | None
    user_agent: str | None
