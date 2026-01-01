from typing import Iterable
from fastapi import Request

ADMIN_ROLES = {"administrateur", "responsable_fae", "back_office_fae"}
USER_ADMIN_ROLES = {"administrateur"}
DASHBOARD_ROLES = {"administrateur", "responsable_fae"}
USER_VIEW_ROLES = {"administrateur", "responsable_fae"}


def get_user_roles(request: Request) -> set[str]:
    roles = getattr(request.state, "user_roles", set())
    if not roles:
        return set()
    return set(roles)


def has_any_role(request: Request, roles: Iterable[str]) -> bool:
    role_set = set(roles)
    if not role_set:
        return False
    return bool(get_user_roles(request) & role_set)
