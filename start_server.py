#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de démarrage du serveur avec vérifications"""

import sys
import os

print("=" * 60)
print("Démarrage du serveur Flask - Projet Pacte")
print("=" * 60)

# Vérification des imports
try:
    from flask import Flask
    print("✓ Flask installé")
except ImportError as e:
    print(f"✗ ERREUR: Flask n'est pas installé")
    print(f"  Exécutez: pip install -r requirements.txt")
    sys.exit(1)

try:
    from flask_sqlalchemy import SQLAlchemy
    print("✓ Flask-SQLAlchemy installé")
except ImportError as e:
    print(f"✗ ERREUR: Flask-SQLAlchemy n'est pas installé")
    print(f"  Exécutez: pip install Flask-SQLAlchemy")
    sys.exit(1)

try:
    from flask_login import LoginManager
    print("✓ Flask-Login installé")
except ImportError as e:
    print(f"✗ ERREUR: Flask-Login n'est pas installé")
    print(f"  Exécutez: pip install Flask-Login")
    sys.exit(1)

# Vérification de la base de données
db_path = os.path.join('instance', 'gestion_salles.db')
if not os.path.exists(db_path):
    print(f"⚠ Base de données non trouvée: {db_path}")
    print("  Vous devrez peut-être exécuter: python init_db.py")

# Import de l'application
try:
    from app import app
    print("✓ Application Flask chargée avec succès")
except Exception as e:
    print(f"✗ ERREUR lors du chargement de l'application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("Serveur démarré avec succès!")
print("=" * 60)
print("\n📍 Accédez à l'application sur:")
print("   http://localhost:5000")
print("\n⚠ Pour arrêter le serveur, appuyez sur Ctrl+C")
print("=" * 60 + "\n")

# Démarrage du serveur
if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\nServeur arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n✗ ERREUR lors du démarrage: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
















