"""Pick the UI language from the host: georgeai.de is German, everything else English.

Django's own admin and Jazzmin ship German catalogs, so activating "de" is all
the admin needs. Runs instead of LocaleMiddleware on purpose: the domain is the
language choice here, not the browser's Accept-Language header.
"""
from django.utils import translation

GERMAN_HOSTS = ("georgeai.de", "www.georgeai.de")


def language_for_host(host):
    host = (host or "").split(":")[0].lower()
    return "de" if host in GERMAN_HOSTS or host.endswith(".georgeai.de") else "en"


class HostLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = language_for_host(request.get_host())
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        translation.deactivate()
        return response
