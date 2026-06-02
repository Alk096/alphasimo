from formulaire.forms import SessionForm
from formulaire.models import Utilisateur
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Prefetch, Count, F
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
    # programmes = models.Programme.objects.filter(
    #     sessions__date_debut__gte=timezone.localdate()
    # ).prefetch_related(
    #     Prefetch('sessions', queryset=models.Session.objects.filter(date_debut__gte=timezone.localdate()))
    # ).distinct()
    programmes = models.Programme.objects.all().prefetch_related(
        Prefetch('sessions', queryset=models.Session.objects.all())
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
        messages.error(request, "Cette session n'est plus disponible. Veuillez effectuer une demande sur mesure.")
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
                # Send credentials via email
                subject = "Vos identifiants Alpha Simo"
                message = f"Bonjour {user.first_name},\n\nVotre compte a été créé avec succès.\nIdentifiant (email) : {user.email}\nMot de passe temporaire : {pwd}\n\nVeuillez vous connecter et changer votre mot de passe.\n\nCordialement,\nL'équipe Alpha Simo"
                send_mail(subject, message, None, [user.email], fail_silently=False)
            
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

                            # Send credentials via email
                            subject = "Vos identifiants Alpha Simo"
                            message = f"Bonjour {p_user.first_name},\n\nVotre compte a été créé avec succès.\nIdentifiant (email) : {p_user.email}\nMot de passe temporaire : {p_pwd}\n\nVeuillez vous connecter et changer votre mot de passe.\n\nCordialement,\nL'équipe Alpha Simo"
                            send_mail(subject, message, None, [p_user.email], fail_silently=False)
                            
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
            return redirect('Dashboard_user')
            
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
        utlisateur = models.Utilisateur.objects.filter(user=user).first()
        if utlisateur is not None:
            if utlisateur.profil == 'Formateur':
                login(request, user)
                return redirect('Dashboard')
            login(request, user)
            return redirect('Dashboard_user')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    context = {'form': form}
    return render(request, 'connexion.html', context=context)

# ===============================================================
# DECORATEUR POUR VERIFIER LE PROFIL DE L'UTILISATEUR
# ===============================================================

def is_formateur(user):
    utilisateur = models.Utilisateur.objects.filter(user=user).first()
    return utilisateur.profil == 'Formateur'

def is_learner(user):
    utilisateur = models.Utilisateur.objects.filter(user=user).first()
    return utilisateur.profil == 'Learner'

@login_required(login_url='Connexion')
@user_passes_test(is_learner, login_url='Connexion')
def dashboard_user(request):
    programmes = models.Programme.objects.filter(
        sessions__date_debut__gte=timezone.localdate()
    ).prefetch_related(
        Prefetch('sessions', queryset=models.Session.objects.filter(date_debut__gte=timezone.localdate()))
    ).distinct()
    participant = models.Participant.objects.filter(utilisateur__user=request.user).first()
    whatsapp = participant.whatsapp if participant else ''
    mes_inscriptions = models.Inscription.objects.filter(participant=participant)
    mes_sessions = models.Inscription.objects.filter(participant=participant, session__date_debut__gte=timezone.localdate())
    context = {
        'programmes': programmes,
        'whatsapp': whatsapp,
        'mes_inscriptions': mes_inscriptions,
        'mes_sessions': mes_sessions,
    }
    return render(request, 'dashboard_user.html', context=context)


@login_required(login_url='Connexion')
@user_passes_test(is_formateur, login_url='Connexion')
def dashboad(request):
    programmes = models.Programme.objects.all()
    sessions_av = models.Session.objects.filter(date_debut__gte=timezone.localdate())
    sessions = models.Session.objects.filter(date_debut__lt=timezone.localdate())
    inscris = models.Inscription.objects.all().distinct().order_by('participant__utilisateur__user__date_joined')

    context = {
        'programmes':programmes,
        'sessions_av':sessions_av,
        'sessions':sessions,
        'inscris':inscris
    }
    return render(request, 'dashboad.html',context=context)

def programmes(request):
    form = forms.ProgrammeForm()
    programmes = models.Programme.objects.all().prefetch_related('sessions')
    labels = models.Programme.objects.values_list('label', flat=True).distinct()
    total_sessions = models.Session.objects.count()
    sessions_av = models.Session.objects.filter(date_debut__gte=timezone.localdate()).count()
    total_inscriptions = models.Inscription.objects.count()
    context = {
        'programmes': programmes,
        'labels': labels,
        'total_sessions': total_sessions,
        'sessions_av': sessions_av,
        'total_inscriptions': total_inscriptions,
        'form': form
    }
    return render(request, 'programmes.html', context=context)

def add_programme(request):
    if request.method == 'POST':
        form = forms.ProgrammeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    else:
        form = forms.ProgrammeForm()
    return redirect('Programmes_admin')

def edit_programme(request, id):
    programme = models.Programme.objects.get(id=id)
    if request.method == 'POST':
        form = forms.ProgrammeForm(request.POST, request.FILES, instance=programme)
        if form.is_valid():
            form.save()
            return redirect('Programmes_admin')
    else:
        form = forms.ProgrammeForm(programme)
    context = {'form': form}
    return render(request, 'edit_programme.html', context=context)

def delete_programme(request, id):
    programme = models.Programme.objects.get(id=id)
    programme.delete()
    return redirect('Programmes_admin')

def sessions(request):
    form = forms.SessionForm()
    sessions = models.Session.objects.all().prefetch_related('programme').order_by('-date_debut')

    programme_id = request.GET.get('programme')
    lieu = request.GET.get('lieu')
    statut = request.GET.get('statut')

    if programme_id:
        sessions = sessions.filter(programme_id=programme_id)

    if lieu:
        sessions = sessions.filter(lieu=lieu)

    today = timezone.localdate()
    if statut == 'ouverte':
        sessions = sessions.filter(date_debut__gte=today)
    elif statut == 'complete':
        sessions = sessions.annotate(inscrits=Count('inscription_set')).filter(inscrits__gte=F('nombre_de_place'))
    elif statut == 'terminee':
        sessions = sessions.filter(date_fin__lt=today)

    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if query_params.get('page'):
        query_params.pop('page')
    querystring = query_params.urlencode()

    programmes = models.Programme.objects.all()

    context = {
        'sessions': page_obj,
        'form': form,
        'programmes': programmes,
        'selected_programme': programme_id,
        'selected_lieu': lieu,
        'selected_statut': statut,
        'page_obj': page_obj,
        'querystring': querystring,
    }
    return render(request, 'sessions.html', context=context)

def add_session(request):
    form = forms.SessionForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect('Sessions_admin')
    else:
        form = forms.SessionForm()
        return redirect('Sessions_admin')

def edit_session(request, id):
    print("Hi")
    if request.method == 'POST':
        print("Post")
        session = models.Session.objects.get(id=id)
        form = forms.SessionForm(request.POST, instance=session)
        if form.is_valid():
            print("Damned")
            form.save()
            return redirect('Sessions_admin')
    return redirect('Sessions_admin')

def delete_session(request, id):
    session = models.Session.objects.get(id=id)
    session.delete()
    return redirect('Sessions_admin')

def demandes_admin(request):
    return redirect('Dashboard')
    return render(request, 'demandes_admin.html')