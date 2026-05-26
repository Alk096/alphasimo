from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Utilisateur(models.Model):
    PROFILS = [
        ('Formateur', 'Formateur'),
        ('Learner', 'Learner'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profil = models.CharField(max_length=9, choices=PROFILS, default='Learner')

    def __str__(self):
        return self.user.first_name+" "+self.user.last_name

class Entreprise(models.Model):
    raison = models.CharField(max_length=100, null=False, blank=False)
    adresse = models.CharField(max_length=200, null=True, blank=True)
    secteur = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.raison

class Programme(models.Model):
    label = models.CharField(max_length=20, null=False, blank=False)
    titre = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    document = models.FileField(upload_to='Docs/', null=True, blank=True)
    
    def __str__(self):
        return self.titre
    
class Session(models.Model):
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='sessions')
    date_debut = models.DateField()
    date_fin = models.DateField()
    start_time = models.TimeField()
    prix = models.CharField(max_length=20, null=False, blank=False)
    nombre_de_place = models.PositiveIntegerField()
    lieu = models.CharField(max_length=100, choices=[('Lome', 'Lomé'), ('Tunis', 'Tunis')], default='Lome')

    @property
    def is_active(self):
        return self.date_debut >= timezone.localdate()

    @property
    def formatted_date_range(self):
        from django.template.defaultfilters import date as django_date
        if not self.date_debut or not self.date_fin:
            return "À déterminer"
        
        if self.date_debut.month == self.date_fin.month and self.date_debut.year == self.date_fin.year:
            day_start = django_date(self.date_debut, "j")
            end_str = django_date(self.date_fin, "j F Y")
            result = f"{day_start} - {end_str}"
        elif self.date_debut.year != self.date_fin.year:
            start_str = django_date(self.date_debut, "j F Y")
            end_str = django_date(self.date_fin, "j F Y")
            result = f"{start_str} - {end_str}"
        else:
            start_str = django_date(self.date_debut, "j F")
            end_str = django_date(self.date_fin, "j F Y")
            result = f"{start_str} - {end_str}"
            
        return result.title()

    def __str__(self):
        return f"{self.programme.titre} - {self.date_debut} - {self.date_fin}"

class Participant(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    whatsapp = models.CharField(max_length=20, null=False, blank=False)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.SET_NULL, null=True, blank=True)
    poste = models.CharField(max_length=100, null=False, blank=False)
    
    def __str__(self):
        return f"{self.utilisateur.user.first_name} {self.utilisateur.user.last_name}"

class Presence(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    date_presence = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.participant} - {self.session}"

class Inscription(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    session = models.ForeignKey('Session', on_delete=models.CASCADE)
    type = models.CharField(max_length=12, choices=[('individuel', 'Individuel'), ('organisation', 'Organisation')], default='individuel')
    condition = models.BooleanField(default=False)
    statut = models.BooleanField(default=False)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.participant} - {self.session}"

class Demande(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='demandes')
    justification = models.TextField(null=True, blank=True)
    statut = models.BooleanField(default=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.participant} - {self.programme}"

