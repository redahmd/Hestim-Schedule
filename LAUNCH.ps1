# Script de lancement complet
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PROJET PACTE - Lancement" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1: Vérifier Python
Write-Host "[1/4] Verification de Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ERREUR: Python n'est pas installe!" -ForegroundColor Red
    exit 1
}

# Étape 2: Installer les dépendances
Write-Host "`n[2/4] Installation des dependances..." -ForegroundColor Yellow
$packages = @("Flask", "Flask-SQLAlchemy", "Flask-Login", "Werkzeug", "python-dotenv")
foreach ($pkg in $packages) {
    Write-Host "   Installation de $pkg..." -NoNewline
    $output = python -m pip install $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " ERREUR" -ForegroundColor Red
        Write-Host $output
    }
}

# Étape 3: Vérifier Flask
Write-Host "`n[3/4] Verification de Flask..." -ForegroundColor Yellow
try {
    $flaskCheck = python -c "import flask; print(flask.__version__)" 2>&1
    Write-Host "   Flask $flaskCheck installe" -ForegroundColor Green
} catch {
    Write-Host "   ERREUR: Flask n'est pas installe correctement" -ForegroundColor Red
    Write-Host "   Essayez: python -m pip install Flask" -ForegroundColor Yellow
    exit 1
}

# Étape 4: Initialiser la base de données
Write-Host "`n[4/4] Initialisation de la base de donnees..." -ForegroundColor Yellow
if (Test-Path "instance\gestion_salles.db") {
    Write-Host "   Base de donnees existe deja" -ForegroundColor Gray
} else {
    python init_db.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Base de donnees creee" -ForegroundColor Green
    } else {
        Write-Host "   ATTENTION: Erreur lors de la creation de la base" -ForegroundColor Yellow
    }
}

# Démarrer le serveur
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Demarrage du serveur..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Accedez a l'application sur:" -ForegroundColor Cyan
Write-Host "   http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comptes de demonstration:" -ForegroundColor Cyan
Write-Host "   Admin: admin@example.com / admin123" -ForegroundColor White
Write-Host "   Enseignant: jean.dupont@example.com / password123" -ForegroundColor White
Write-Host "   Etudiant: pierre.durand@example.com / password123" -ForegroundColor White
Write-Host ""
Write-Host "⚠ Pour arreter: Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Lancer le serveur
python app.py
















