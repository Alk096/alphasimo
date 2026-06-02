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
    path("Dashboard/Programmes/", views.programmes, name="Programmes_admin"),
    path("Dashboard/Programmes/add/", views.add_programme, name="add_programme"),
    path("Dashboard/Programmes/<int:id>/edit/", views.edit_programme, name="edit_programme"),
    path("Dashboard/Programmes/<int:id>/delete/", views.delete_programme, name="delete_programme"),

    path("Dashboard/Sessions/", views.sessions, name="Sessions_admin"),
    path("Dashboard/Sessions/add/", views.add_session, name="add_session"),
    path("Dashboard/Sessions/<int:id>/edit/", views.edit_session, name="edit_session"),
    path("Dashboard/Sessions/<int:id>/delete/", views.delete_session, name="delete_session"),

    path("Dashboard/Demandes/", views.demandes_admin, name="Demandes_admin")

]