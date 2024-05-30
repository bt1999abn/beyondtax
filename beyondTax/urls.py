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
from django.urls import path, include
from django.conf import settings

from accounts.api.views import GoogleLoginApi
from . import views

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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
