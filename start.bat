@echo off
echo ========================================
echo Demarrage du serveur Projet Pacte
echo ========================================
echo.

REM Vérifier si Python est disponible
py --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

REM Installer les dépendances si nécessaire
echo Installation des dependances...
py -m pip install Flask Flask-SQLAlchemy Flask-Login Werkzeug python-dotenv --quiet

REM Vérifier Flask
py -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Flask n'a pas pu etre installe
    echo Essayez manuellement: pip install Flask
    pause
    exit /b 1
)

REM Initialiser la base de données si nécessaire
if not exist "instance\gestion_salles.db" (
    echo Initialisation de la base de donnees...
    py init_db.py
)

REM Démarrer le serveur
echo.
echo ========================================
echo Serveur en cours de demarrage...
echo ========================================
echo.
echo Accedez a l'application sur: http://localhost:5000
echo Pour arreter, appuyez sur Ctrl+C
echo.
echo ========================================
echo.

py app.py

pause
















