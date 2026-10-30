from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.utils import timezone


class NoCacheAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response["Cache-Control"] = "no-store, no-cache, private"
        return response


class SessionInactivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ahora = timezone.now().timestamp()
            ultima = request.session.get("_ultima_actividad")
            if ultima and ahora - ultima > settings.SESSION_COOKIE_AGE:
                logout(request)
                request.session.flush()
                return redirect(settings.LOGIN_URL)
            request.session["_ultima_actividad"] = ahora
        return self.get_response(request)


class FriendlyMethodNotAllowedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 405 and not getattr(response, "streaming", False):
            return render(request, "405.html", status=405)
        return response
