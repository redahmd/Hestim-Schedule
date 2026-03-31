# Guide de Démarrage Rapide

## 🚀 Installation et Lancement

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Initialiser la base de données
```bash
python init_db.py
```

Cette commande va :
- Créer toutes les tables de la base de données
- Ajouter des données de démonstration (utilisateurs, professeurs, groupes, salles, cours, réservations)

### 3. Lancer l'application
```bash
python app.py
```

L'application sera accessible sur : **http://localhost:5000**

## 👤 Se connecter

Utilisez l'un des comptes de démonstration :

### Administrateur
- **Email**: `admin@example.com`
- **Mot de passe**: `admin123`

### Enseignant
- **Email**: `jean.dupont@example.com`
- **Mot de passe**: `password123`

### Étudiant
- **Email**: `pierre.durand@example.com`
- **Mot de passe**: `password123`

## 📋 Fonctionnalités disponibles

### Pour tous les utilisateurs
- ✅ Consultation des salles disponibles
- ✅ Consultation des cours
- ✅ Consultation des réservations (selon le rôle)
- ✅ Tableau de bord personnalisé

### Pour les Administrateurs et Enseignants
- ✅ Créer une nouvelle réservation
- ✅ Modifier une réservation
- ✅ Annuler une réservation

### Détection automatique des conflits
L'application détecte automatiquement :
- ⚠️ Conflit de salle (même salle, même créneau)
- ⚠️ Conflit de professeur (même professeur, même créneau)
- ⚠️ Conflit de groupe (même groupe, même créneau)
- ⚠️ Capacité insuffisante (effectif du groupe > capacité de la salle)

## 🔄 Réinitialiser la base de données

Si vous voulez réinitialiser la base de données avec des données propres :
```bash
python init_db.py
```

⚠️ **Attention**: Cela supprimera toutes les données existantes !

## 🐛 Dépannage

### Erreur "Module not found"
Assurez-vous d'avoir installé toutes les dépendances :
```bash
pip install -r requirements.txt
```

### Erreur de base de données
Supprimez le fichier `gestion_salles.db` et réinitialisez :
```bash
rm gestion_salles.db  # Sur Linux/Mac
del gestion_salles.db  # Sur Windows
python init_db.py
```

### Le port 5000 est déjà utilisé
Modifiez le port dans `app.py` :
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Changez 5000 en 5001
```

## 📚 Documentation

Consultez le fichier `README.md` pour plus de détails sur :
- La structure du projet
- L'architecture de la base de données
- Les technologies utilisées
- Les fonctionnalités détaillées

## 🎯 Prochaines étapes (Semestre 2)

Pour le Semestre 2, il faudra ajouter :
- Module d'analyse et statistiques
- Génération automatique des emplois du temps
- Visualisation avec graphiques (Chart.js, Plotly)
- Déploiement en production

