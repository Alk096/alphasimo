from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.formulaire, name='formulaire'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('dashboad/', views.dashboad, name='dashboad'),
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard_data'),
]