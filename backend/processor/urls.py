from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_dataset, name='process_dataset'),
]