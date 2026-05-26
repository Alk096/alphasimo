from dataclasses import field
from django import forms
from . import models
import random
import string

def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

class connexionForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    fields = ['email', 'password']

class InscriptionForm(forms.Form):
    # champs de l'utilisateur
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100)
    email = forms.EmailField()
    whatsapp = forms.CharField(max_length=20)

    # champs entreprise (optionnels par défaut, gérés dans la vue)
    raison = forms.CharField(max_length=100, required=False)
    adresse = forms.CharField(max_length=200, required=False)
    secteur = forms.CharField(max_length=100, required=False)

    # champs participant (optionnels par défaut, gérés dans la vue)
    poste = forms.CharField(max_length=100, required=False)


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = models.Entreprise
        fields = '__all__'

class SessionForm(forms.ModelForm):
    class Meta:
        model = models.Session
        fields = '__all__'

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = models.Participant
        fields = '__all__'

class PresenceForm(forms.ModelForm):
    class Meta:
        model = models.Presence
        fields = '__all__'

class DemandeForm(forms.ModelForm):
    class Meta:
        model = models.Demande
        fields = '__all__'
