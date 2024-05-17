from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from api.views import redirect_to_recipe

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path(
        "s/<slug:short_code>/", redirect_to_recipe,
        name="redirect-to-recipe"
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)
