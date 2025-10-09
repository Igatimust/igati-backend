
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/<str:email>/<str:password>/', views.login, name='login')
]