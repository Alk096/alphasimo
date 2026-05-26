from django.contrib import admin
from django.contrib.auth.models import User
from . import models

# Register your models here.
admin.site.register(models.Utilisateur)
admin.site.register(models.Entreprise)
admin.site.register(models.Programme)
admin.site.register(models.Session)
admin.site.register(models.Participant)
admin.site.register(models.Presence)
admin.site.register(models.Inscription)
admin.site.register(models.Demande)

