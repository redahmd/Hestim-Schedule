from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models import Professeur, Cours, Utilisateur

professeurs_bp = Blueprint('professeurs', __name__)

@professeurs_bp.route('/')
@login_required
def liste():
    """Liste des professeurs (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard.home'))
    
    recherche = request.args.get('recherche', '')
    query = Professeur.query
    
    if recherche:
        query = query.filter(
            db.or_(
                Professeur.nom.contains(recherche),
                Professeur.prenom.contains(recherche),
                Professeur.email.contains(recherche),
                Professeur.specialite.contains(recherche)
            )
        )
    
    professeurs = query.order_by(Professeur.nom, Professeur.prenom).all()
    
    for prof in professeurs:
        prof.nb_cours = Cours.query.filter_by(id_professeur=prof.id_professeur).count()
        
    return render_template('professeurs/liste.html', professeurs=professeurs, recherche=recherche)

@professeurs_bp.route('/creer', methods=['GET', 'POST'])
@login_required
def creer():
    """Ajouter un professeur"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('professeurs.liste'))
    
    if request.method == 'POST':
        try:
            nom = request.form.get('nom')
            prenom = request.form.get('prenom')
            email = request.form.get('email')
            specialite = request.form.get('specialite')
            telephone = request.form.get('telephone')
            departement = request.form.get('departement')
            
            if not all([nom, prenom, email]):
                flash('Nom, prénom et email sont obligatoires.', 'error')
                return render_template('professeurs/creer.html')
            
            if Professeur.query.filter_by(email=email).first():
                flash('Un professeur avec cet email existe déjà.', 'error')
                return render_template('professeurs/creer.html')
            
            nouveau_prof = Professeur(
                nom=nom,
                prenom=prenom,
                email=email,
                specialite=specialite,
                telephone=telephone,
                departement=departement,
                actif=True
            )
            
            db.session.add(nouveau_prof)
            
            # Créer aussi le compte utilisateur pour le login
            if not Utilisateur.query.filter_by(email=email).first():
                nouveau_user = Utilisateur(
                    nom=nom,
                    prenom=prenom,
                    email=email,
                    role='enseignant',
                    actif=True
                )
                nouveau_user.set_password('hestim2024') # Mot de passe par défaut
                db.session.add(nouveau_user)
                flash('Professeur et compte utilisateur (mdp: hestim2024) créés avec succès.', 'success')
            else:
                flash('Professeur créé. Un compte utilisateur avec cet email existait déjà.', 'warning')
            
            db.session.commit()
            
            return redirect(url_for('professeurs.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('professeurs/creer.html')

@professeurs_bp.route('/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(id):
    """Modifier un professeur"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('professeurs.liste'))
    
    prof = Professeur.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            
            if email != prof.email and Professeur.query.filter_by(email=email).first():
                flash('Un autre professeur utilise déjà cet email.', 'error')
                return render_template('professeurs/modifier.html', prof=prof)
            
            prof.nom = request.form.get('nom')
            prof.prenom = request.form.get('prenom')
            prof.email = email
            prof.specialite = request.form.get('specialite')
            prof.telephone = request.form.get('telephone')
            prof.departement = request.form.get('departement')
            prof.actif = request.form.get('actif') == 'on'
            
            # Mettre à jour l'utilisateur associé si l'email correspond
            user = Utilisateur.query.filter_by(email=prof.email).first() # Ancien email
            if user:
                 user.nom = prof.nom
                 user.prenom = prof.prenom
                 user.email = email
                 user.actif = prof.actif
            
            db.session.commit()
            flash('Professeur et compte utilisateur modifiés avec succès.', 'success')
            return redirect(url_for('professeurs.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
            
    return render_template('professeurs/modifier.html', prof=prof)

@professeurs_bp.route('/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    """Supprimer un professeur"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('professeurs.liste'))
    
    try:
        prof = Professeur.query.get_or_404(id)
        
        # Vérifier s'il a des cours
        nb_cours = Cours.query.filter_by(id_professeur=id).count()
        if nb_cours > 0:
            flash(f'Impossible de supprimer ce professeur car il est associé à {nb_cours} cours.', 'error')
            return redirect(url_for('professeurs.liste'))
            
        # Supprimer aussi l'utilisateur associé
        user = Utilisateur.query.filter_by(email=prof.email).first()
        if user:
            db.session.delete(user)
            
        db.session.delete(prof)
        db.session.commit()
        flash('Professeur et compte utilisateur supprimés avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
        
    return redirect(url_for('professeurs.liste'))

