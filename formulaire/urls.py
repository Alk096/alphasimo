from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.accueil_view, name='Accueil'),
    path('Programmes/', views.programme, name='Programme'),
    path('Inscription/<int:id>/',views.formulaire,name='Inscription'),
    path('connexion/', views.user_connexion, name='connexion'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard_user/', views.dashboard_user, name='dashboard_user'),
    path('Dashboard/', views.dashboad, name='dashboad'),
    path('Inscription/', views.inscription, name='inscription'),
]