from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Prospect(models.Model):
    # Information personnelle
    prenom = models.CharField(max_length=50)
    nom = models.CharField(max_length=50)
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
    programme_souhaiter = models.CharField(max_length=100, choices=CHOIX_PROGRAMME)
    session_preferee = models.DateField()
    lieu_souhaiter = models.CharField(max_length=100, choices=LIEU_SOUHAITER)
    
    # Besoins spécifiques
    besoin_specifique = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.entreprise} - {self.lieu_souhaiter} - {self.session_preferee} - {self.besoin_specifique}"
