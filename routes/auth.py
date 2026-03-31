from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database import db
from models import Utilisateur

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        selected_role = request.form.get('role')

        if not email or not password or not selected_role:
            flash('Veuillez remplir tous les champs, y compris le rôle', 'error')
            return render_template('auth/login.html')

        user = Utilisateur.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.actif:
                if user.role == 'administrateur' and user.email != 'admin@hestim.ma':
                    flash("Votre compte administrateur est en attente d'approbation par le super-admin.", 'error')
                else:
                    flash('Votre compte est désactivé', 'error')
                return render_template('auth/login.html')

            # Vérifier la cohérence entre le rôle choisi et celui du compte
            if user.role != selected_role:
                flash('Le rôle sélectionné ne correspond pas à votre compte.', 'error')
                return render_template('auth/login.html')

            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.home'))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role', 'etudiant')
        
        # Validation
        if not all([nom, prenom, email, password]):
            flash('Veuillez remplir tous les champs', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return render_template('auth/register.html')
        
        if Utilisateur.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'error')
            return render_template('auth/register.html')
        
        # Création de l'utilisateur
        is_admin = (role == 'administrateur')
        is_master = (email == 'admin@hestim.ma')
        user = Utilisateur(
            nom=nom,
            prenom=prenom,
            email=email,
            role=role,
            actif=not is_admin or is_master
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Inscription réussie ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Une erreur est survenue lors de l\'inscription', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('auth.login'))


