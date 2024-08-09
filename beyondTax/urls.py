"""
URL configuration for beyondTax project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from accounts.api.views import GoogleLoginApi
from . import views

schema_view = get_schema_view(
   openapi.Info(
      title="BeyondTax API",
      default_version='v1',
      description="API documentation for BeyondTax",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@beyondtax.co"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny,],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/api/login/google/', GoogleLoginApi.as_view(), name='google_login'),
    path('service-dummy-api/', views.ServiceDummyApiView.as_view(), name='service-dummy-api'),
    path('mobilenumber-dummy-api/', views.MobileNumberDummyApi.as_view(), name='mobilenumber-dummy-api'),
    path('verifyotp-dummy-api/', views.VerifyOtpDummyApi.as_view(), name='verifyotp-dummy-api'),

    # Django JET dashboard URLS
    path(r'jet/', include('shared.libs.external.jet.urls', 'jet')),  # Django JET URLS
    path(r'jet/dashboard/', include('shared.libs.external.jet.dashboard.urls', 'jet-dashboard')),
    # Django JET dashboard URLS
    path('accounts/',include('accounts.urls')),
    path('beyondTaxServices/', include('beyondTaxServices.urls')),
    path('workorder/', include('workOrder.urls')),
    path('incomeTax/', include('services.incomeTax.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('blogs/', include('blogs.urls')),
    path('payments/',include('payments.urls')),
    #swagger urls
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
