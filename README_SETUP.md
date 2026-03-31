# Guide d'installation - Projet Pacte

## Installation rapide

### 1. Installer les dépendances

```powershell
python -m pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug python-dotenv
```

Ou avec le fichier requirements.txt :
```powershell
python -m pip install -r requirements.txt
```

### 2. Initialiser la base de données

```powershell
python init_db.py
```

Cela créera :
- Les tables de la base de données
- Des utilisateurs de démonstration
- Des salles, cours, groupes et réservations d'exemple

### 3. Démarrer le serveur

```powershell
python app.py
```

Le serveur sera accessible sur : **http://localhost:5000**

## Comptes de démonstration

Après l'initialisation, vous pouvez vous connecter avec :

- **Administrateur** : `admin@example.com` / `admin123`
- **Enseignant** : `prof@example.com` / `password123`
- **Étudiant** : `etudiant@example.com` / `password123`

## Structure du projet

```
Projet Pacte/
├── app.py                 # Application Flask principale
├── config.py              # Configuration
├── database.py            # Configuration SQLAlchemy
├── models.py              # Modèles de données
├── init_db.py             # Script d'initialisation
├── routes/                # Blueprints Flask
│   ├── auth.py
│   ├── dashboard.py
│   ├── salles.py
│   ├── reservations.py
│   └── cours.py
├── templates/             # Templates Jinja2
│   ├── base.html
│   ├── index.html
│   └── ...
├── static/                # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── Logo.png
└── instance/              # Base de données SQLite
    └── gestion_salles.db
```

## Dépannage

### Flask n'est pas installé
```powershell
python -m pip install --upgrade pip
python -m pip install Flask Flask-SQLAlchemy Flask-Login
```

### Erreur de base de données
Supprimez le fichier `instance/gestion_salles.db` et réexécutez `python init_db.py`

### Port déjà utilisé
Modifiez le port dans `app.py` (ligne 70) : `app.run(debug=True, host='0.0.0.0', port=5001)`
















