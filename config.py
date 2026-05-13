import os
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

class Config:
    """Configuration de l'application Flask"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///gestion_salles.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

