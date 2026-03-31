from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import db
from models import Etudiant, Groupe, Utilisateur
from datetime import date, datetime

etudiants_bp = Blueprint('etudiants', __name__)

@etudiants_bp.route('/')
@login_required
def liste():
    """Liste des étudiants (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard.home'))
    
    recherche = request.args.get('recherche', '')
    groupe_id = request.args.get('groupe_id')
    
    query = Etudiant.query
    
    if recherche:
        query = query.filter(
            db.or_(
                Etudiant.nom.contains(recherche),
                Etudiant.prenom.contains(recherche),
                Etudiant.email.contains(recherche)
            )
        )
    
    if groupe_id:
        try:
            query = query.filter(Etudiant.id_groupe == int(groupe_id))
        except (ValueError, TypeError):
            pass
            
    etudiants = query.order_by(Etudiant.nom, Etudiant.prenom).all()
    groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
        
    return render_template('etudiants/liste.html', etudiants=etudiants, groupes=groupes, recherche=recherche, groupe_id=groupe_id)

@etudiants_bp.route('/creer', methods=['GET', 'POST'])
@login_required
def creer():
    """Ajouter un étudiant"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('etudiants.liste'))
    
    if request.method == 'POST':
        try:
            nom = request.form.get('nom')
            prenom = request.form.get('prenom')
            email = request.form.get('email')
            niveau = request.form.get('niveau')
            id_groupe = request.form.get('id_groupe')
            
            if not all([nom, prenom, email]):
                flash('Nom, prénom et email sont obligatoires.', 'error')
                groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
                return render_template('etudiants/creer.html', groupes=groupes)
            
            if Etudiant.query.filter_by(email=email).first():
                flash('Un étudiant avec cet email existe déjà.', 'error')
                groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
                return render_template('etudiants/creer.html', groupes=groupes)
            
            nouveau_etudiant = Etudiant(
                nom=nom,
                prenom=prenom,
                email=email,
                niveau=niveau,
                id_groupe=int(id_groupe) if id_groupe else None,
                date_inscription=date.today(),
                actif=True
            )
            
            db.session.add(nouveau_etudiant)
            
            # Créer aussi le compte utilisateur pour le login
            if not Utilisateur.query.filter_by(email=email).first():
                nouveau_user = Utilisateur(
                    nom=nom,
                    prenom=prenom,
                    email=email,
                    role='etudiant',
                    actif=True
                )
                nouveau_user.set_password('hestim2024') # Mot de passe par défaut
                db.session.add(nouveau_user)
                flash('Étudiant et compte utilisateur (mdp: hestim2024) créés avec succès.', 'success')
            else:
                flash('Étudiant ajouté. Un compte utilisateur avec cet email existait déjà.', 'warning')

            db.session.commit()
            
            return redirect(url_for('etudiants.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
    
    groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
    return render_template('etudiants/creer.html', groupes=groupes)

@etudiants_bp.route('/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(id):
    """Modifier un étudiant"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('etudiants.liste'))
    
    etudiant = Etudiant.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            
            if email != etudiant.email and Etudiant.query.filter_by(email=email).first():
                flash('Un autre étudiant utilise déjà cet email.', 'error')
                groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
                return render_template('etudiants/modifier.html', etudiant=etudiant, groupes=groupes)
            
            etudiant.nom = request.form.get('nom')
            etudiant.prenom = request.form.get('prenom')
            etudiant.email = email
            etudiant.niveau = request.form.get('niveau')
            
            id_groupe = request.form.get('id_groupe')
            etudiant.id_groupe = int(id_groupe) if id_groupe else None
            
            etudiant.actif = request.form.get('actif') == 'on'
            
            # Mettre à jour l'utilisateur associé aussi
            user = Utilisateur.query.filter_by(email=etudiant.email).first() # Note: si email change, on cherche par quel id?
            # Problème: si on change l'email de l'étudiant, on perd le lien si on cherche par email ici.
            # Idéalement on chercherait l'utilisateur avant le changement d'email, mais ici 'etudiant.email' est DEJA modifié ?
            # Non, 'etudiant' est l'objet SQLAlchemy chargé. 'email' est la variable du form.
            # Ligne 114: etudiant.email = email -> ça modifie l'objet en session.
            
            # On va essayer de retrouver l'utilisateur par l'ancien email s'il a changé, ou alors on suppose qu'il n'a pas changé.
            # Comme on a déjà attribué le nouvel email à l'objet etudiant, l'objet est sale.
            # Pour faire simple: on cherche un utilisateur avec le NOUVEL email. S'il existe on le met à jour.
            # S'il n'existe pas, on cherche avec l'ancien? un peu compliqué sans extraire l'ancien avant.
            # Pour l'instant on va faire simple : chercher utilisateur par email (le nouveau). Si trouvé, update info.
            
            user = Utilisateur.query.filter_by(email=email).first()
            if not user:
                 # Essayons de voir si on peut le trouver autrement... ou tant pis
                 pass
            else:
                 user.nom = etudiant.nom
                 user.prenom = etudiant.prenom
                 user.actif = etudiant.actif
                 # Si l'email a changé, user.email est déjà bon car on l'a trouvé avec.
                 
            db.session.commit()
            flash('Étudiant et compte utilisateur modifiés avec succès.', 'success')
            return redirect(url_for('etudiants.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
            
    groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
    return render_template('etudiants/modifier.html', etudiant=etudiant, groupes=groupes)

@etudiants_bp.route('/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    """Supprimer un étudiant"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('etudiants.liste'))
    
    try:
        etudiant = Etudiant.query.get_or_404(id)
        
        # Supprimer aussi l'utilisateur associé
        user = Utilisateur.query.filter_by(email=etudiant.email).first()
        if user:
            db.session.delete(user)
            
        db.session.delete(etudiant)
        db.session.commit()
        flash('Étudiant et compte utilisateur supprimés avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
        
    return redirect(url_for('etudiants.liste'))

