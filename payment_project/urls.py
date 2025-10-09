"""
URL configuration for payment_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        'message': 'Payment System API',
        'version': '1.0',
        'endpoints': {
            'initialize_payment': 'POST /api/payments/initialize/',
            'payment_callback': 'GET /api/payments/callback/?reference=XXX',
            'check_status': 'GET /api/payments/status/<reference>/',
            'list_payments': 'GET /api/payments/list/',
        },
        'documentation': '/api/payments/docs/',
        'status': 'running'
    })

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/payments/', include('payments.urls')),
]
