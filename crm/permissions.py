from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsOperatorAssignedOrManager(permissions.BasePermission):
    """Allow safe methods for authenticated users.
    For unsafe methods: allow managers/superusers, or operators assigned to the lead.
    Works with `Lead`, `Task`, `Note` objects that have a `lead` attribute (or are Lead themselves).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            logger.info(f"has_permission: user not auth")
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        # Managers can perform write operations
        is_superuser = request.user.is_superuser
        is_crm_manager = request.user.groups.filter(name='CRM Manager').exists()
        logger.info(f"has_permission: user={request.user}, is_superuser={is_superuser}, is_crm_manager={is_crm_manager}")
        if is_superuser or is_crm_manager:
            return True
        # For create operations without object context, restrict unless overridden in view
        return False

    def has_object_permission(self, request, view, obj):
        logger.info(f"has_object_permission: user={request.user}, method={request.method}, obj={obj}")
        if request.method in permissions.SAFE_METHODS:
            return True
        # Managers can write
        if request.user.is_superuser or request.user.groups.filter(name='CRM Manager').exists():
            return True
        # Determine the related lead
        lead = obj if getattr(obj, 'stage', None) is not None else getattr(obj, 'lead', None)
        if lead is None:
            return False
        return lead.assignee_id == request.user.id
