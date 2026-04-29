"""
URL configuration for QLVB project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path(
        "admin/login/",
        RedirectView.as_view(
            pattern_name="admin_login_redirect",
            query_string=True,
            permanent=False,
        ),
    ),
    path("", include("QLVBDH.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
