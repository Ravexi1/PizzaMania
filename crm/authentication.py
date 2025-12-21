from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """SessionAuthentication without CSRF checks for API endpoints."""
    
    def enforce_csrf(self, request):
        return  # Skip CSRF check
