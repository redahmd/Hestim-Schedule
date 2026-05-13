# Plateforme de Gestion de Salles "Hestim Schedule" - Projet PACTE

Application web de gestion et réservation de salles pour la planification automatique des cours, la gestion des réservations de salles, et la synchronisation des emplois du temps des enseignants et étudiants.

## 🚀 Fonctionnalités

🔐 Gestion des Utilisateurs & Rôles
➜ ✅ Double Authentification : Connexion sécurisée via Flask-Login avec protection des routes.
➜ ✅ Multi-Rôles : Espaces dédiés pour Administrateurs, Enseignants et Étudiants.
➜ ✅ Profil Avancé : Gestion du profil utilisateur avec option de changement de mot de passe.
➜ ✅ Système d'Approbation : Validation manuelle des comptes administrateurs par le Super-Admin.
📅 Planification & Gestion de Calendrier
➜ ✅ CRUD Complet : Création, modification et suppression dynamique des réservations.
➜ ✅ Planning Global : Visualisation par calendrier avec filtres intelligents (Prof, Salle, Groupe).
➜ ✅ Cycle de Validation : Workflow de réservation (En attente ➜ Confirmée ➜ Annulée).
➜ ✅ Génération Automatique : Outil intelligent pour assister la création rapide du planning.
🛡️ Algorithme Anti-Conflits (Intelligent)
➜ 🟢 Conflit Salle : Blocage automatique si une salle est déjà occupée sur le créneau.
➜ 🟢 Conflit Professeur : Empêche un enseignant d'être assigné à deux cours différents simultanément.
➜ 🟢 Conflit Groupe : Garantit qu'un groupe d'étudiants n'a qu'un seul cours à la fois.
➜ 🟢 Vérification Capacité : Alerte si l'effectif du groupe dépasse la capacité réelle de la salle.
📊 Analyse de Données & KPIs (Data Science)
➜ ✅ Dashboard Analytique : Visualisation en temps réel via Chart.js (Donuts, Barres, Lignes).
➜ ✅ Heatmaps d'Occupation : Analyse visuelle des pics de fréquentation par heure et par jour.
➜ ✅ Matrice de Corrélation : Analyse Pandas croisant les types de salles et les jours de la semaine.
➜ ✅ Expertise Excel : Exportation automatique de tous les rapports au format .xlsx pour archivage.
💎 Design & Expérience Utilisateur (Premium UI)
➜ 🟢 Aesthétique Moderne : Interface fluide avec effets de transparence "Glassmorphism".
➜ 🟢 Navigation Intuitive : Sidebar dynamique et Header intelligent (Sticky NavBar).
➜ 🟢 Alertes Temps Réel : Système de notifications Toasts et centre de notifications centralisé.
➜ 🟢 Full Responsive : Expérience utilisateur parfaite sur Mobile, Tablette et Desktop.
📂 Administration des Ressources
➜ ✅ Gestion Salles : Monitoring complet des équipements (Capacité, Type, Bâtiment).
➜ ✅ Gestion Académique : Administration des étudiants par promotion et des cours par code.

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
  - Email: `prof@example.com`
  - Mot de passe: `password123`

- **Étudiant**: 
  - Email: `etudiant@example.com`
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


## 🛠️ Technologies utilisées

- **Backend**: Flask 3.0
- **Base de données**: SQLite / SQLAlchemy
- **Frontend**: Bootstrap 5, HTML5, CSS3
- **Authentification**: Flask-Login
- **Icons**: Bootstrap Icons

## 📄 Licence

Ce projet est développé dans le cadre du projet PACTE - Cycle Ingénieur 2025/2026.

## 👥 Auteur

Équipe de développement - Projet PACTE :
Reda Hamidi

