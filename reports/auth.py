# reports/auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import SAFE_METHODS, BasePermission

# -------------------------------
# RBAC roles + permission helpers
# -------------------------------

ROLE_VIEWER = "viewer"
ROLE_EDITOR = "editor"
ROLE_ADMIN = "admin"

def user_role(user):
    """
    Resolve a coarse role from built-in flags and Django groups.
    - admin:     superuser
    - editor:    in 'Editor' group (case-insensitive) OR is_staff
    - viewer:    in 'Viewer' group; default for unauthenticated users
    """
    # Anonymous/unauthenticated → viewer
    if not getattr(user, "is_authenticated", False):
        return ROLE_VIEWER

    # Superuser → admin
    if getattr(user, "is_superuser", False):
        return ROLE_ADMIN

    # Groups
    try:
        names = set(user.groups.values_list("name", flat=True))
    except Exception:
        names = set()
    lower = {str(n).lower() for n in names}

    if "editor" in lower:
        return ROLE_EDITOR
    if "viewer" in lower:
        return ROLE_VIEWER

    # Fallback: staff behaves like editor; everyone else viewer
    return ROLE_EDITOR if getattr(user, "is_staff", False) else ROLE_VIEWER


class IsViewerReadOnly(BasePermission):
    """
    Allows SAFE methods (GET/HEAD/OPTIONS) for all roles (including anonymous via LenientJWT).
    Blocks write operations unless user is editor/admin.
    Use this on ViewSets where reads are publicly visible but writes must be gated.
    """
    def has_permission(self, request, view):
        role = user_role(request.user)
        if request.method in SAFE_METHODS:
            return True
        return role in (ROLE_EDITOR, ROLE_ADMIN)


class IsEditorOrAdmin(BasePermission):
    """
    Strict gate: only editor/admin can access this view at all (both read and write).
    Use this for endpoints that should not be visible to viewers.
    """
    def has_permission(self, request, view):
        return user_role(request.user) in (ROLE_EDITOR, ROLE_ADMIN)


# ---------------------------------------
# Existing lenient JWT auth (keep intact)
# ---------------------------------------

class LenientJWTAuthentication(JWTAuthentication):
    """
    If the Authorization header is empty/garbage, allow GET/HEAD/OPTIONS to pass
    as anonymous instead of 401. Writes still require a valid token.

    This plays nicely with IsViewerReadOnly: anonymous GETs are treated as "viewer".
    """
    def authenticate(self, request):
        raw = (request.META.get("HTTP_AUTHORIZATION") or "").strip()

        # Common bad dev headers we should ignore
        if raw in ("Bearer", "Bearer null", "Bearer undefined", "Bearer None"):
            return None

        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            # Don’t block read-only requests if the token is bad/missing
            if request.method in SAFE_METHODS:
                return None
            raise
