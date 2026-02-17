# JWT verification and RBAC middleware — implemented in Sprint 1.
# This module will provide:
#   - decode_jwt(token: str) -> dict
#   - get_current_user(token) -> User dependency
#   - require_role(*roles) -> FastAPI dependency
