from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import Config
from database import db

# Initialisation de l'application
app = Flask(__name__)
app.config.from_object(Config)

# Initialisation des extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'info'

# Import des modèles (doit être après db)
from models import *

# Import des blueprints
from routes.auth import auth_bp
from routes.salles import salles_bp
from routes.reservations import reservations_bp
from routes.cours import cours_bp
from routes.dashboard import dashboard_bp
from routes.professeurs import professeurs_bp
from routes.etudiants import etudiants_bp

# Enregistrement des blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(salles_bp, url_prefix='/salles')
app.register_blueprint(reservations_bp, url_prefix='/reservations')
app.register_blueprint(cours_bp, url_prefix='/cours')
app.register_blueprint(dashboard_bp, url_prefix='/')
app.register_blueprint(professeurs_bp, url_prefix='/professeurs')
app.register_blueprint(etudiants_bp, url_prefix='/etudiants')

@app.route('/')
def landing():
    """Redirection vers le dashboard ou login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return redirect(url_for('auth.login'))

@app.context_processor
def inject_notifications():
    """Injecte les notifications non lues et le rôle dans tous les templates."""
    from models import Notification
    from sqlalchemy.exc import OperationalError, ProgrammingError

    if current_user.is_authenticated:
        try:
            # Vérifier si la table existe en essayant une requête simple
            unread_query = Notification.query.filter_by(
                id_utilisateur=current_user.id_utilisateur,
                lu=False
            ).order_by(Notification.date_envoi.desc())

            notifications_unread = unread_query.limit(5).all()
            notifications_unread_count = unread_query.count()
        except (OperationalError, ProgrammingError) as e:
            # La table n'existe pas encore ou erreur de base de données
            # Retourner des valeurs par défaut pour éviter de bloquer l'application
            notifications_unread = []
            notifications_unread_count = 0
        except Exception:
            # Autre erreur inattendue, retourner des valeurs par défaut
            notifications_unread = []
            notifications_unread_count = 0
    else:
        notifications_unread = []
        notifications_unread_count = 0

    return {
        "notifications_unread": notifications_unread,
        "notifications_unread_count": notifications_unread_count,
    }

@login_manager.user_loader
def load_user(user_id):
    from models import Utilisateur
    return Utilisateur.query.get(int(user_id))

# Note: Utilisez init_db.py pour initialiser la base de données
# @app.before_first_request est déprécié dans Flask 3.0

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


