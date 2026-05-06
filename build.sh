#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py makemigrations

python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --no-input

# Migration de la base de données
python manage.py migrate