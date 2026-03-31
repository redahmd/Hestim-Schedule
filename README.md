# Plateforme de Gestion de Salles - Projet PACTE

Application web de gestion et réservation de salles pour la planification automatique des cours, la gestion des réservations de salles, et la synchronisation des emplois du temps des enseignants et étudiants.

## 🚀 Fonctionnalités

### Semestre 1 (Implémenté)
- ✅ Authentification et gestion des rôles (Administrateur, Enseignant, Étudiant)
- ✅ Consultation des salles disponibles avec filtres
- ✅ Planification de cours (création, modification, annulation)
- ✅ Détection automatique des conflits de réservation
  - Conflit de salle (même salle, même créneau)
  - Conflit de professeur (même professeur, même créneau)
  - Conflit de groupe (même groupe, même créneau)
- ✅ Vérification de la capacité des salles
- ✅ Interface web moderne avec Bootstrap 5

## 📋 Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

## 🔧 Installation

1. **Cloner ou télécharger le projet**

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialiser la base de données**
   ```bash
   python init_db.py
   ```
   Ce script va créer toutes les tables et ajouter des données de démonstration.

4. **Lancer l'application**
   ```bash
   python app.py
   ```

5. **Accéder à l'application**
   Ouvrez votre navigateur à l'adresse: `http://localhost:5000`

## 👤 Comptes de démonstration

Après l'initialisation de la base de données, vous pouvez vous connecter avec:

- **Administrateur**: 
  - Email: `admin@example.com`
  - Mot de passe: `admin123`

- **Enseignant**: 
  - Email: `jean.dupont@example.com`
  - Mot de passe: `password123`

- **Étudiant**: 
  - Email: `pierre.durand@example.com`
  - Mot de passe: `password123`

## 📁 Structure du projet

```
Projet Pacte/
├── app.py                 # Application Flask principale
├── config.py              # Configuration de l'application
├── models.py              # Modèles de données SQLAlchemy
├── init_db.py             # Script d'initialisation de la base de données
├── requirements.txt       # Dépendances Python
├── routes/                # Blueprints Flask
│   ├── auth.py           # Authentification
│   ├── dashboard.py      # Tableau de bord
│   ├── salles.py         # Gestion des salles
│   ├── reservations.py   # Gestion des réservations
│   └── cours.py          # Gestion des cours
├── templates/             # Templates HTML
│   ├── base.html         # Template de base
│   ├── auth/             # Templates d'authentification
│   ├── dashboard/        # Templates du tableau de bord
│   ├── salles/           # Templates des salles
│   ├── reservations/     # Templates des réservations
│   └── cours/            # Templates des cours
└── static/               # Fichiers statiques (CSS, JS)
```

## 🗄️ Base de données

L'application utilise SQLite par défaut (fichier `gestion_salles.db`). Le schéma de base de données comprend:

- **utilisateur**: Comptes utilisateurs avec authentification
- **professeur**: Informations sur les professeurs
- **groupe**: Groupes d'étudiants
- **etudiant**: Informations sur les étudiants
- **salle**: Caractéristiques des salles
- **cours**: Définition des cours
- **creneau**: Créneaux horaires
- **reservation**: Réservations (table centrale)
- **disponibilite_professeur**: Disponibilités des professeurs
- **notification**: Notifications système
- **audit_log**: Journal d'audit

## 🎯 Utilisation

### Pour les Administrateurs
- Accès complet à toutes les fonctionnalités
- Consultation de toutes les réservations
- Statistiques globales

### Pour les Enseignants
- Créer et modifier leurs réservations
- Consulter leurs cours et réservations
- Voir les salles disponibles

### Pour les Étudiants
- Consulter les réservations de leur groupe
- Voir les salles disponibles
- Consulter l'emploi du temps

## 🔒 Sécurité

- Mots de passe hashés avec Werkzeug
- Gestion des sessions avec Flask-Login
- Protection CSRF (à implémenter pour la production)
- Validation des données côté serveur

## 📝 Notes

- Cette application est un prototype pour le Semestre 1
- Pour la production, il faudrait:
  - Ajouter la protection CSRF
  - Utiliser une base de données plus robuste (PostgreSQL, MySQL)
  - Implémenter les tests unitaires
  - Ajouter la gestion des erreurs avancée
  - Déployer sur un serveur de production

## 🛠️ Technologies utilisées

- **Backend**: Flask 3.0
- **Base de données**: SQLite / SQLAlchemy
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Authentification**: Flask-Login
- **Icons**: Bootstrap Icons

## 📄 Licence

Ce projet est développé dans le cadre du projet PACTE - Cycle Ingénieur 2025/2026.

## 👥 Auteur

Équipe de développement - Projet PACTE

