from django.urls import path
from . import views

app_name = 'rutas'

urlpatterns = [
    path('crear/', views.crear_ruta, name='crear_ruta'),
]