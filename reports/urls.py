from django.urls import path
from . import views

urlpatterns = [
    path('export/', views.export_data_api, name='export-data'),
]