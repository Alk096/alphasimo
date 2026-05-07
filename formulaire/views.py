from django.shortcuts import render, redirect
from .forms import ProspectForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .models import Prospect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

def formulaire(request):
    if request.method == 'POST':
        form = ProspectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre inscription a été enregistrée avec succès !")
            return redirect('formulaire')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = ProspectForm()
    
    return render(request, 'formulaire.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboad') 
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            
    return render(request, 'login.html')

@login_required(login_url='login')
def dashboad(request):
    return render(request, 'dashboad.html')

@login_required(login_url='login')
def api_dashboard_data(request):
    # Filters
    lieu = request.GET.get('lieu')
    programme = request.GET.get('programme')
    session = request.GET.get('session')

    prospects_query = Prospect.objects.all().order_by('-created_at')

    if lieu:
        prospects_query = prospects_query.filter(lieu_souhaiter=lieu)
    if programme:
        prospects_query = prospects_query.filter(programme_souhaiter=programme)
    if session:
        prospects_query = prospects_query.filter(session_preferee=session)

    # KPIs calculation
    total_count = prospects_query.count()
    lome_count = prospects_query.filter(lieu_souhaiter='Lomé').count()
    tunis_count = prospects_query.filter(lieu_souhaiter='Tunis').count()
    group_count = prospects_query.filter(besoin_specifique=True).count()
    group_pct = round((group_count / total_count * 100), 1) if total_count > 0 else 0

    # Chart data
    chart_data = prospects_query.values('programme_souhaiter').annotate(count=Count('id'))
    chart_dict = {
        'qse_count': prospects_query.filter(programme_souhaiter='QSE').count(),
        'mgmt_count': prospects_query.filter(programme_souhaiter='Management').count(),
        'audit_count': prospects_query.filter(programme_souhaiter='Audit').count(),
    }

    # Latest 4 for notifications
    latest_prospects = prospects_query[:4]
    latest_data = []
    for p in latest_prospects:
        latest_data.append({
            'prenom': p.prenom,
            'nom': p.nom,
            'programme': p.get_programme_souhaiter_display(),
            'lieu': p.lieu_souhaiter,
            'entreprise': p.entreprise,
        })

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(prospects_query, 8)
    page_obj = paginator.get_page(page_number)

    # Table data
    table_data = []
    for p in page_obj:
        table_data.append({
            'initials': f"{p.prenom[0]}{p.nom[0]}".upper(),
            'prenom': p.prenom,
            'nom': p.nom,
            'number': p.number,
            'email_pro': p.email_pro,
            'entreprise': p.entreprise,
            'poste': p.poste,
            'secteur': p.secteur,
            'programme': p.get_programme_souhaiter_display(),
            'session': p.session_preferee.strftime('%b %Y') if p.session_preferee else '',
            'lieu': p.lieu_souhaiter,
            'besoin_specifique': p.besoin_specifique,
        })

    return JsonResponse({
        'kpis': {
            'total': total_count,
            'lome_count': lome_count,
            'tunis_count': tunis_count,
            'group_pct': group_pct,
        },
        'chart': chart_dict,
        'latest': latest_data,
        'unread_count': Prospect.objects.filter(is_read=False).count(),
        'prospects': table_data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'per_page': paginator.per_page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'total_items': total_count,
        }
    })

@login_required(login_url='login')
def mark_notifications_as_read(request):
    if request.method == 'POST':
        Prospect.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)