# Script PowerShell pour installer les dépendances et initialiser la base de données

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation des dépendances Flask" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Installation des packages
$packages = @(
    "Flask==3.0.0",
    "Flask-SQLAlchemy==3.1.1",
    "Flask-Login==0.6.3",
    "Werkzeug==3.0.1",
    "python-dotenv==1.0.0"
)

foreach ($package in $packages) {
    Write-Host "Installation de $package..." -ForegroundColor Yellow
    python -m pip install $package
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $package installé" -ForegroundColor Green
    } else {
        Write-Host "✗ Erreur lors de l'installation de $package" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Vérification de Flask" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

python -c "import flask; print('Flask version:', flask.__version__)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Flask n'est pas installé correctement" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Initialisation de la base de données" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

python init_db.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✅ Configuration terminée!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`n📋 Comptes de démonstration:" -ForegroundColor Cyan
    Write-Host "   Admin: admin@example.com / admin123"
    Write-Host "   Enseignant: jean.dupont@example.com / password123"
    Write-Host "   Étudiant: pierre.durand@example.com / password123"
    Write-Host "`n🚀 Pour démarrer: python app.py" -ForegroundColor Yellow
} else {
    Write-Host "✗ Erreur lors de l'initialisation" -ForegroundColor Red
    exit 1
}
















