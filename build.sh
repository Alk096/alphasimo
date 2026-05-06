#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Collecte des fichiers statiques
python manage.py collectstatic --no-input

# Migration de la base de données
python manage.py migrate