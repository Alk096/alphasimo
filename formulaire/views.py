from django.shortcuts import render, redirect
from .forms import ProspectForm
from django.contrib import messages
from django.contrib.auth import authenticate, login

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


def dashboad(request):
    return render(request, 'dashboad.html')