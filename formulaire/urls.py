from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.accueil_view, name='Accueil'),
    path('Programmes/', views.programme, name='Programme'),
    path('Inscription/<int:id>/',views.formulaire,name='Inscription'),
    path('Connexion/', views.user_connexion, name='Connexion'),
    path('Logout/', auth_views.LogoutView.as_view(), name='Logout'),
    path('Dashboard_user/', views.dashboard_user, name='Dashboard_user'),
    path('Dashboard/', views.dashboad, name='Dashboard'),
]