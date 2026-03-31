# Script complet de configuration et démarrage
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuration Projet Pacte" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Étape 1: Créer l'environnement virtuel
Write-Host "`n[1/5] Création de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "   Environnement virtuel existe déjà" -ForegroundColor Gray
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ERREUR: Impossible de créer l'environnement virtuel" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✓ Environnement virtuel créé" -ForegroundColor Green
}

# Étape 2: Activer l'environnement virtuel
Write-Host "`n[2/5] Activation de l'environnement virtuel..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERREUR: Impossible d'activer l'environnement virtuel" -ForegroundColor Red
    Write-Host "   Essayez: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✓ Environnement virtuel activé" -ForegroundColor Green

# Étape 3: Mettre à jour pip
Write-Host "`n[3/5] Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "   ✓ pip mis à jour" -ForegroundColor Green

# Étape 4: Installer les dépendances
Write-Host "`n[4/5] Installation des dépendances..." -ForegroundColor Yellow
$packages = @(
    "Flask==3.0.0",
    "Flask-SQLAlchemy==3.1.1",
    "Flask-Login==0.6.3",
    "Werkzeug==3.0.1",
    "python-dotenv==1.0.0"
)

foreach ($package in $packages) {
    Write-Host "   Installation de $package..." -ForegroundColor Gray
    python -m pip install $package --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ERREUR lors de l'installation de $package" -ForegroundColor Red
        exit 1
    }
}
Write-Host "   ✓ Toutes les dépendances installées" -ForegroundColor Green

# Étape 5: Vérifier Flask
Write-Host "`n[5/5] Vérification de l'installation..." -ForegroundColor Yellow
python -c "import flask; print('   Flask version:', flask.__version__)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERREUR: Flask n'est pas installé correctement" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ Flask installé correctement" -ForegroundColor Green

# Initialiser la base de données
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Initialisation de la base de données" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERREUR lors de l'initialisation de la base de données" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ Configuration terminée!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`n📋 Comptes de démonstration:" -ForegroundColor Cyan
Write-Host "   Admin: admin@example.com / admin123"
Write-Host "   Enseignant: jean.dupont@example.com / password123"
Write-Host "   Étudiant: pierre.durand@example.com / password123"
Write-Host "`n🚀 Démarrage du serveur..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Démarrer le serveur
python app.py
















