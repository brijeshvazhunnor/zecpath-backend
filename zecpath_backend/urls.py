from django.contrib import admin
from django.urls import path, include
from apps.core.views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.core.urls")),
]