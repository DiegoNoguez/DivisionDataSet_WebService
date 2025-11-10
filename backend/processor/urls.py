from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_dataset, name='process_dataset'),
    path('health/', views.health_check, name='health_check'),  # Nuevo endpoint
]