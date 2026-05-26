from formulaire.models import Utilisateur
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from . import forms, models
import random, string

def accueil_view(request):
    programmes = models.Programme.objects.filter(
        sessions__date_debut__gte=timezone.localdate()
    ).prefetch_related(
        Prefetch('sessions', queryset=models.Session.objects.filter(date_debut__gte=timezone.localdate()))
    ).distinct()[:3]
    context = {
        "programmes":programmes
    }
    return render(request, 'accueil.html', context=context)

def programme(request):
    programmes = models.Programme.objects.filter(
        sessions__date_debut__gte=timezone.localdate()
    ).prefetch_related(
        Prefetch('sessions', queryset=models.Session.objects.filter(date_debut__gte=timezone.localdate()))
    ).distinct()
    labels = models.Programme.objects.distinct().values_list('label', flat=True).distinct()
    context = {
        "programmes":programmes,
        "labels":labels
    }
    return render(request, 'programme.html', context=context)

def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def formulaire(request, id):
    session = models.Session.objects.get(id=id)
    if not session.is_active:
        return redirect('Programme')
    
    # Calculer le nombre de places restantes
    session.restant = session.nombre_de_place - models.Inscription.objects.filter(session=session).count()
    form = forms.InscriptionForm()
    
    if request.method == 'POST':
        form = forms.InscriptionForm(request.POST)
        registration_type = request.POST.get('registration_type', 'individuel')
        
        is_valid = form.is_valid()
        custom_errors = []
        
        if is_valid:
            # Validation personnalisée selon le type d'inscription
            if registration_type == 'organisation':
                raison = request.POST.get('org_name') or form.cleaned_data.get('raison')
                if not raison:
                    form.add_error('raison', "Le nom de l'organisation est requis pour une inscription en organisation.")
                    is_valid = False
                
                # Empêcher l'inscription multiple pour l'inscrivant principal
                email_main_clean = form.cleaned_data['email'].strip()
                if models.Inscription.objects.filter(participant__utilisateur__user__email=email_main_clean, session=session).exists():
                    form.add_error('email', "L'inscrivant principal (contact) est déjà inscrit à cette session.")
                    is_valid = False
                
                # Vérifier qu'il y a au moins un participant valide
                p_firstnames = request.POST.getlist('p_firstname[]')
                p_lastnames = request.POST.getlist('p_lastname[]')
                p_emails = request.POST.getlist('p_email[]')
                
                has_participant = False
                for i in range(len(p_emails)):
                    if (i < len(p_firstnames) and i < len(p_lastnames) and 
                        p_firstnames[i].strip() and p_lastnames[i].strip() and p_emails[i].strip()):
                        has_participant = True
                        break
                
                if not has_participant:
                    custom_errors.append("Pour une inscription d'organisation, vous devez enregistrer au moins un participant avec prénom, nom et email.")
                    is_valid = False
                else:
                    # Empêcher les inscriptions multiples pour les participants de la liste
                    for i in range(len(p_emails)):
                        email_clean = p_emails[i].strip()
                        if email_clean and models.Inscription.objects.filter(participant__utilisateur__user__email=email_clean, session=session).exists():
                            custom_errors.append(f"Le participant avec l'email '{email_clean}' est déjà inscrit à cette session.")
                            is_valid = False
            else:
                # Inscription individuelle : le poste de la personne est requis
                poste = form.cleaned_data.get('poste') or request.POST.get('position')
                if not poste:
                    form.add_error('poste', "Le poste/fonction est requis pour une inscription individuelle.")
                    is_valid = False
                
                # Empêcher l'inscription multiple pour l'individu
                email_clean = form.cleaned_data['email'].strip()
                if models.Inscription.objects.filter(participant__utilisateur__user__email=email_clean, session=session).exists():
                    form.add_error('email', "Vous êtes déjà inscrit à cette session.")
                    is_valid = False

        if is_valid:
            # 1. Créer ou récupérer le User principal (le contact)
            user, created = User.objects.get_or_create(
                email=form.cleaned_data['email'].strip(),
                defaults={
                    'username': form.cleaned_data['email'].strip(),
                    'first_name': form.cleaned_data['prenom'],
                    'last_name': form.cleaned_data['nom'],
                }
            )
            if created:
                pwd = random_password()
                user.set_password(pwd)
                print("Mot de passe : ", pwd)
                user.save()
            
            # Profil Utilisateur
            utilisateur, _ = models.Utilisateur.objects.get_or_create(
                user=user,
                defaults={'profil': 'Learner'}
            )
            
            # 2. Créer ou obtenir l'entreprise (si organisation)
            entreprise = None
            if registration_type == 'organisation':
                org_name = request.POST.get('org_name') or form.cleaned_data.get('raison')
                entreprise, _ = models.Entreprise.objects.get_or_create(
                    raison=org_name.strip(),
                    defaults={'secteur': form.cleaned_data.get('secteur', '')}
                )
            
            # 3. Créer le(s) Participant(s) et les Inscriptions
            if registration_type == 'organisation':
                # Le participant contact (celui qui remplit le formulaire) doit aussi être lié à l'entreprise
                contact_participant, p_created = models.Participant.objects.get_or_create(
                    utilisateur=utilisateur,
                    defaults={
                        'whatsapp': form.cleaned_data['whatsapp'],
                        'entreprise': entreprise,
                        'poste': form.cleaned_data.get('poste') or request.POST.get('position', '')
                    }
                )
                if not p_created:
                    contact_participant.entreprise = entreprise
                    contact_participant.poste = form.cleaned_data.get('poste') or request.POST.get('position', '')
                    contact_participant.save()

                # Inscrire également l'inscrivant principal à la session
                models.Inscription.objects.create(
                    participant=contact_participant,
                    session=session,
                    type='organisation',
                    condition=True,
                    statut=False
                )

                p_firstnames = request.POST.getlist('p_firstname[]')
                p_lastnames = request.POST.getlist('p_lastname[]')
                p_emails = request.POST.getlist('p_email[]')
                p_positions = request.POST.getlist('p_position[]')
                
                for i in range(len(p_emails)):
                    if (i < len(p_firstnames) and i < len(p_lastnames) and 
                        p_firstnames[i].strip() and p_lastnames[i].strip() and p_emails[i].strip()):
                        
                        p_user, p_created = User.objects.get_or_create(
                            email=p_emails[i].strip(),
                            defaults={
                                'username': p_emails[i].strip(),
                                'first_name': p_firstnames[i].strip(),
                                'last_name': p_lastnames[i].strip(),
                            }
                        )
                        if p_created:
                            p_pwd = random_password()
                            p_user.set_password(p_pwd)
                            p_user.save()
                            
                        p_utilisateur, _ = models.Utilisateur.objects.get_or_create(
                            user=p_user,
                            defaults={'profil': 'Learner'}
                        )
                        
                        p_participant, p_part_created = models.Participant.objects.get_or_create(
                            utilisateur=p_utilisateur,
                            defaults={
                                'whatsapp': form.cleaned_data['whatsapp'],
                                'entreprise': entreprise,
                                'poste': p_positions[i].strip() if i < len(p_positions) else ''
                            }
                        )
                        if not p_part_created:
                            p_participant.entreprise = entreprise
                            p_participant.poste = p_positions[i].strip() if i < len(p_positions) else ''
                            p_participant.save()
                        
                        models.Inscription.objects.create(
                            participant=p_participant,
                            session=session,
                            type='organisation',
                            condition=True,
                            statut=False
                        )
            else:
                # Inscription individuelle
                participant, p_created = models.Participant.objects.get_or_create(
                    utilisateur=utilisateur,
                    defaults={
                        'whatsapp': form.cleaned_data['whatsapp'],
                        'entreprise': None,
                        'poste': form.cleaned_data.get('poste') or request.POST.get('position', '')
                    }
                )
                if not p_created:
                    participant.poste = form.cleaned_data.get('poste') or request.POST.get('position', '')
                    participant.save()
                
                models.Inscription.objects.create(
                    participant=participant,
                    session=session,
                    type='individuel',
                    condition=True,
                    statut=False
                )
                
            messages.success(request, "Votre inscription a bien été enregistrée.")
            return redirect('dashboard_user')
            
        else:
            for error in custom_errors:
                messages.error(request, error)
                
    context = {'form': form, 'session': session}
    return render(request, 'formulaire.html', context=context)

def user_connexion(request):
    form = forms.connexionForm()
    if request.method == 'POST':
        form = forms.connexionForm(request.POST)
        email = form.data.get('email')
        password = form.data.get('password')
        
        user = authenticate(request, username=email, password=password)
        utlisateur = models.Utilisateur(user=user)
        if utlisateur is not None:
            if utlisateur.profil == 'Formateur':
                login(request, user)
                return redirect('dashboad')
            login(request, user)
            return redirect('dashboard_user')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    context = {'form': form}
    return render(request, 'connexion.html', context=context)

def inscription(request):
    return 1

@login_required(login_url='connexion')
# @user_passes_test(lambda u: u.is_admin)
def dashboad(request):
    return render(request, 'dashboad.html')

@login_required(login_url='connexion')
# @user_passes_test(lambda u: not u.is_admin)
def dashboard_user(request):
    programmes = models.Programme.objects.prefetch_related('sessions').all()
    for p in programmes:
        p.first_session = p.sessions.all().order_by('date_debut').first()
        if p.first_session:
            p.date_debut = p.first_session.date_debut
            p.date_fin = p.first_session.date_fin
            p.total_prix = p.first_session.prix
        else:
            p.date_debut = None
            p.date_fin = None
            p.total_prix = 0

    context = {
        'programmes': programmes,
        'programmes_count': programmes.count(),
    }
    return render(request, 'dashboard_user.html', context=context)