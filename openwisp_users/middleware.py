import time

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, logout
from django.shortcuts import redirect
from django.urls import resolve, reverse_lazy
from django.utils.translation import gettext_lazy as _

from . import settings as app_settings


class PasswordExpirationMiddleware:
    exempted_url_names = [
        "account_change_password",
        "admin:logout",
        "account_logout",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
    ]
    admin_login_path = reverse_lazy("admin:login")
    admin_index_path = reverse_lazy("admin:index")
    account_change_password_path = reverse_lazy("account_change_password")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if the user is authenticated and their password has expired
        if (
            request.user.is_authenticated
            and request.user.has_password_expired()
            # We use `resolve()` here to get the `url_name` from the `request.path`.
            # This is more flexible than using `reverse()` as it doesn't require
            # passing arguments to get the correct path.
            and resolve(request.path).url_name not in self.exempted_url_names
        ):
            messages.warning(
                request,
                _("Your password has expired, please update your password."),
            )
            redirect_path = self.account_change_password_path
            if request.user.is_staff:
                next_path = (
                    request.path
                    if request.path != self.admin_login_path
                    else self.admin_index_path
                )
                redirect_path = f"{redirect_path}?{REDIRECT_FIELD_NAME}={next_path}"
            return redirect(redirect_path)
        return response
class SessionInactivityMiddleware:
    """
    Tracks user activity and automatically logs out users
    who have been inactive for longer than SESSION_INACTIVITY_TIMEOUT.
    Stores last activity timestamp in the session.
    """

    login_url = reverse_lazy("two_factor:login")
    exempted_url_names = [
        "admin:login",
        "login",
        "account_login",
        "account_logout",
        "account_reset_password",
        "account_reset_password_done",
        "account_reset_password_from_key",
        "account_reset_password_from_key_done",
        "session_activity",
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = app_settings.SESSION_INACTIVITY_TIMEOUT

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        url_name = resolve(request.path).url_name
        if url_name in self.exempted_url_names:
            return self.get_response(request)

        now = time.time()
        last_activity = request.session.get("last_activity")

        if last_activity and (now - last_activity) > self.timeout:
            # Clear session data and mark for deletion instead of calling
            # logout(), which flushes the session and causes
            # SessionInterrupted with cache-based session backends.
            request.session.clear()
            request.session.cycle_key()
            return redirect(f"{self.login_url}?session_expired=1")

        # Update last activity timestamp on every request
        request.session["last_activity"] = now

        return self.get_response(request)
