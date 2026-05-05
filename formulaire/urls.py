from django.urls import path
from . import views
urlpatterns = [
    path('', views.formulaire, name='formulaire')
]