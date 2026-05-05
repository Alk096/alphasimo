from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class Prospect(models.Model):
    # Information personnelle
    full_name = models.CharField(max_length=100)
    # International number format
    number = models.CharField(max_length=15)
    email_pro = models.EmailField()

    # Information professionnelle
    entreprise = models.CharField(max_length=100)
    poste = models.CharField(max_length=100)
    secteur = models.CharField(max_length=100)

    # Choix du programme
    CHOIX_PROGRAMME = [
        ('QSE', ' QSE Qualifiant'),
        ('Management', 'Management des Processus'),
        ('Audit', 'Audit Interne'),
    ]

    LIEU_SOUHAITER = [
        ('Lomé', 'Lomé'),
        ('Tunis', 'Tunis'),
    ]
    programme_souhaiter = models.CharField(max_length=100)
    session_preferee = models.DateField()
    lieu_souhaiter = models.CharField(max_length=100)
    
    # Besoins spécifiques
    besoin_specifique = models.BooleanField()
