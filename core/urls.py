"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from home.views.error_views import not_found
from api import urls as api_url

urlpatterns = [
    path("", include("home.urls")),
    path("admin/", admin.site.urls),
    path("material/", include("theme_material_kit.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/", include(api_url)),
    path("api/v2/", include("api.urls_v2")),
    path("accounts/login/", not_found),
    path("accounts/signup/", not_found),
    path("accounts/", include("allauth.urls")),
]

handler404 = "home.views.error_views.not_found"
handler403 = "home.views.error_views.unauthenticated"
