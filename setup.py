#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script d'installation et d'initialisation complète"""

import subprocess
import sys
import os

def install_requirements():
    """Installe les dépendances"""
    print("=" * 60)
    print("Installation des dépendances...")
    print("=" * 60)
    
    requirements = [
        'Flask==3.0.0',
        'Flask-SQLAlchemy==3.1.1',
        'Flask-Login==0.6.3',
        'Werkzeug==3.0.1',
        'python-dotenv==1.0.0'
    ]
    
    for package in requirements:
        print(f"Installation de {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✓ {package} installé")
        except subprocess.CalledProcessError:
            print(f"✗ Erreur lors de l'installation de {package}")
            return False
    
    return True

def init_database():
    """Initialise la base de données"""
    print("\n" + "=" * 60)
    print("Initialisation de la base de données...")
    print("=" * 60)
    
    try:
        from init_db import init_database
        init_database()
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n🚀 Configuration du projet Projet Pacte\n")
    
    # Vérifier si Flask est déjà installé
    try:
        import flask
        print("✓ Flask est déjà installé")
    except ImportError:
        print("⚠ Flask n'est pas installé, installation en cours...")
        if not install_requirements():
            print("\n✗ Échec de l'installation des dépendances")
            sys.exit(1)
    
    # Initialiser la base de données
    if not init_database():
        print("\n✗ Échec de l'initialisation de la base de données")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Configuration terminée avec succès!")
    print("=" * 60)
    print("\n📋 Comptes de démonstration créés:")
    print("   👤 Admin: admin@example.com / admin123")
    print("   👨‍🏫 Enseignant: jean.dupont@example.com / password123")
    print("   👨‍🎓 Étudiant: pierre.durand@example.com / password123")
    print("\n🚀 Pour démarrer le serveur:")
    print("   python app.py")
    print("\n🌐 Puis ouvrez: http://localhost:5000")
    print("=" * 60 + "\n")
















