from django.shortcuts import render, redirect
from .forms import ProspectForm
from django.contrib import messages

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
