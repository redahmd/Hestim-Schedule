#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script qui installe les dépendances et démarre le serveur"""

import subprocess
import sys
import os

def install_package(package):
    """Installe un package avec pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation de {package}")
        return False

def check_and_install():
    """Vérifie et installe les dépendances"""
    packages = [
        'Flask==3.0.0',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-Login==0.6.3',
        'Werkzeug==3.0.1',
        'python-dotenv==1.0.0'
    ]
    
    print("=" * 60)
    print("Vérification des dépendances...")
    print("=" * 60)
    
    # Vérifier Flask
    try:
        import flask
        print(f"✓ Flask {flask.__version__} est déjà installé")
    except ImportError:
        print("⚠ Flask n'est pas installé, installation en cours...")
        for package in packages:
            print(f"  Installation de {package}...")
            if install_package(package):
                print(f"  ✓ {package} installé")
            else:
                print(f"  ✗ Erreur avec {package}")
                return False
    
    # Vérifier les autres packages
    try:
        import flask_sqlalchemy
        import flask_login
        print("✓ Toutes les dépendances sont installées")
        return True
    except ImportError as e:
        print(f"✗ Dépendance manquante: {e}")
        return False

def init_db():
    """Initialise la base de données"""
    print("\n" + "=" * 60)
    print("Initialisation de la base de données...")
    print("=" * 60)
    
    try:
        from init_db import init_database
        init_database()
        return True
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def start_server():
    """Démarre le serveur Flask"""
    print("\n" + "=" * 60)
    print("Démarrage du serveur Flask...")
    print("=" * 60)
    print("\n📍 Accédez à l'application sur: http://localhost:5000")
    print("⚠ Pour arrêter, appuyez sur Ctrl+C\n")
    print("=" * 60 + "\n")
    
    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    if not check_and_install():
        print("\n✗ Échec de l'installation des dépendances")
        print("Essayez manuellement: pip install -r requirements.txt")
        sys.exit(1)
    
    # Initialiser la base de données si nécessaire
    db_path = os.path.join('instance', 'gestion_salles.db')
    if not os.path.exists(db_path) or os.path.getsize(db_path) < 1000:
        if not init_db():
            print("\n⚠ Base de données non initialisée, mais le serveur peut démarrer")
    
    # Démarrer le serveur
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\nServeur arrêté")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
















