from django.shortcuts import render

def formulaire(request):
    return render(request, 'formulaire.html')
