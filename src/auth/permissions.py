from enum import IntEnum
from typing import Set, Dict


class AccessLevel(IntEnum):
    USER = 1
    LOCAL_LEADER = 2
    ADMIN = 9
    SUPERADMIN = 10


class Permission:
    # Base permissions
    VIEW_DASHBOARD = "view_dashboard"
    PERFORM_ATTRIBUTION = "perform_attribution"

    # Advanced permissions
    SHOW_COLLECTOR_NAME = "show_collector_name"

    # Admin permissions
    ADMIN_HUB = "admin_hub"
    LIST_USERS = "list_users"
    MANAGE_CD_USERS = "manage_cd_users"

    # Superadmin permissions
    MANAGE_ALL_CDS = "manage_all_cds"
    CREATE_ADMINS = "create_admins"


class PermissionManager:
    # Permissions specific to each level
    _LEVEL_PERMISSIONS: Dict[AccessLevel, Set[str]] = {
        AccessLevel.USER: {
            Permission.VIEW_DASHBOARD,
            Permission.PERFORM_ATTRIBUTION,
        },
        AccessLevel.LOCAL_LEADER: {
            Permission.SHOW_COLLECTOR_NAME,
        },
        AccessLevel.ADMIN: {
            Permission.ADMIN_HUB,
            Permission.LIST_USERS,
            Permission.MANAGE_CD_USERS,
        },
        AccessLevel.SUPERADMIN: {
            Permission.MANAGE_ALL_CDS,
            Permission.CREATE_ADMINS,
        },
    }

    # Hierarchy: which level inherits from which
    # USER (1) -> LOCAL_LEADER (2) -> ADMIN (9) -> SUPERADMIN (10)
    _INHERITANCE = {
        AccessLevel.LOCAL_LEADER: AccessLevel.USER,
        AccessLevel.ADMIN: AccessLevel.LOCAL_LEADER,
        AccessLevel.SUPERADMIN: AccessLevel.ADMIN,
    }

    @classmethod
    def get_permissions(cls, level: int) -> Set[str]:
        """Returns the complete set of permissions for a given level, including inherited ones."""
        try:
            current_level = AccessLevel(level)
        except ValueError:
            # If level is not in enum, find the highest level it reaches
            # This handles levels like 3, 4, 5 etc if they ever exist
            valid_levels = sorted([l for l in AccessLevel], reverse=True)
            current_level = AccessLevel.USER
            for l in valid_levels:
                if level >= l:
                    current_level = l
                    break

        permissions = set()

        # Walk up the inheritance chain
        while current_level:
            permissions.update(cls._LEVEL_PERMISSIONS.get(current_level, set()))
            current_level = cls._INHERITANCE.get(current_level)

        return permissions

    @classmethod
    def has_permission(cls, user_level: int, permission: str) -> bool:
        """Checks if a user level has a specific permission."""
        return permission in cls.get_permissions(user_level)
