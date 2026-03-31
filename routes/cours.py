from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database import db
from models import Cours, Professeur, Groupe
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import OperationalError, ProgrammingError

cours_bp = Blueprint('cours', __name__)

def generer_code_cours(nom_cours, type_cours, semestre=None):
    """Génère automatiquement un code de cours unique"""
    # Extraire les premières lettres du nom (max 3-4 lettres)
    mots = nom_cours.upper().split()
    prefixe = ''.join([m[0] for m in mots[:3]])[:4]
    
    # Ajouter le type de cours
    type_map = {'CM': 'CM', 'TD': 'TD', 'TP': 'TP', 'projet': 'PRJ', 'examen': 'EXM'}
    type_code = type_map.get(type_cours, 'CRS')
    
    # Ajouter le semestre si disponible
    semestre_code = f"{semestre:02d}" if semestre else "01"
    
    # Base du code
    base_code = f"{prefixe}{semestre_code}"
    
    # Vérifier l'unicité et ajouter un numéro si nécessaire
    code_cours = base_code
    compteur = 1
    while Cours.query.filter_by(code_cours=code_cours).first():
        code_cours = f"{base_code}{compteur:02d}"
        compteur += 1
        if compteur > 99:
            # Si on dépasse 99, utiliser un timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%H%M%S")[-4:]
            code_cours = f"{prefixe}{timestamp}"
            break
    
    return code_cours


@cours_bp.route('/')
@login_required
def liste():
    """Liste des cours"""
    try:
        type_cours = request.args.get('type', '')
        recherche = request.args.get('recherche', '')
        professeur_id = request.args.get('professeur_id')
        groupe_id = request.args.get('groupe_id')
        semestre = request.args.get('semestre')

        query = Cours.query.options(
            joinedload(Cours.professeur),
            joinedload(Cours.groupe)
        )

        if type_cours:
            query = query.filter_by(type_cours=type_cours)

        if recherche:
            query = query.filter(
                db.or_(
                    Cours.nom_cours.contains(recherche),
                    Cours.code_cours.contains(recherche)
                )
            )

        if professeur_id:
            try:
                query = query.filter(Cours.id_professeur == int(professeur_id))
            except (ValueError, TypeError):
                pass

        if groupe_id:
            try:
                query = query.filter(Cours.id_groupe == int(groupe_id))
            except (ValueError, TypeError):
                pass

        if semestre:
            try:
                query = query.filter(Cours.semestre == int(semestre))
            except (ValueError, TypeError):
                pass

        # Filtrage selon le rôle
        if current_user.role == 'etudiant':
            from models import Etudiant
            try:
                etudiant = Etudiant.query.filter_by(email=current_user.email).first()
                if etudiant and etudiant.id_groupe:
                    query = query.filter(Cours.id_groupe == etudiant.id_groupe)
            except (OperationalError, ProgrammingError):
                pass
        
        elif current_user.role == 'enseignant':
            try:
                professeur = Professeur.query.filter_by(email=current_user.email).first()
                if professeur:
                    query = query.filter(Cours.id_professeur == professeur.id_professeur)
            except (OperationalError, ProgrammingError):
                pass

        cours_list = query.order_by(Cours.code_cours).all()

    except (OperationalError, ProgrammingError):
        cours_list = []

    # Données pour les filtres
    professeurs = []
    groupes = []
    
    try:
        if current_user.role == 'administrateur':
            professeurs = Professeur.query.order_by(Professeur.prenom, Professeur.nom).all()
            groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
        elif current_user.role == 'enseignant':
            # Pour les enseignants, seulement leurs cours sont visibles
            pass
        else:
            # Pour les étudiants, seulement les groupes sont nécessaires
            groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
    except (OperationalError, ProgrammingError):
        pass

    return render_template(
        'cours/liste.html',
        cours_list=cours_list,
        type_cours=type_cours,
        recherche=recherche,
        professeur_id=professeur_id,
        groupe_id=groupe_id,
        semestre=semestre,
        professeurs=professeurs,
        groupes=groupes,
    )

@cours_bp.route('/<int:id>')
@login_required
def detail(id):
    """Détails d'un cours"""
    try:
        cours = Cours.query.options(
            joinedload(Cours.professeur),
            joinedload(Cours.groupe)
        ).get_or_404(id)
        
        # Réservations associées
        from models import Reservation
        from sqlalchemy.orm import joinedload as res_joinedload
        
        reservations = Reservation.query.options(
            res_joinedload(Reservation.creneau),
            res_joinedload(Reservation.salle)
        ).filter_by(
            id_cours=id,
            statut='confirmee'
        ).all()
        
        return render_template('cours/detail.html', cours=cours, reservations=reservations)
    except (OperationalError, ProgrammingError):
        return redirect(url_for('cours.liste'))
    except Exception:
        return redirect(url_for('cours.liste'))

@cours_bp.route('/creer', methods=['GET', 'POST'])
@login_required
def creer():
    """Créer un nouveau cours (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent créer des cours.', 'error')
        return redirect(url_for('cours.liste'))
    
    if request.method == 'POST':
        try:
            nom_cours = request.form.get('nom_cours', '').strip()
            type_cours = request.form.get('type_cours', '')
            nombre_heures = request.form.get('nombre_heures')
            id_professeur = request.form.get('id_professeur')
            id_groupe = request.form.get('id_groupe')
            semestre = request.form.get('semestre')
            coefficient = request.form.get('coefficient')
            
            # Validation
            if not nom_cours:
                flash('Le nom du cours est requis.', 'error')
                return redirect(url_for('cours.creer'))
            
            if not type_cours or type_cours not in ['CM', 'TD', 'TP', 'projet', 'examen']:
                flash('Type de cours invalide.', 'error')
                return redirect(url_for('cours.creer'))
            
            try:
                nombre_heures = int(nombre_heures) if nombre_heures else 0
                if nombre_heures <= 0:
                    flash('Le nombre d\'heures doit être supérieur à 0.', 'error')
                    return redirect(url_for('cours.creer'))
            except (ValueError, TypeError):
                flash('Nombre d\'heures invalide.', 'error')
                return redirect(url_for('cours.creer'))
            
            try:
                id_professeur = int(id_professeur) if id_professeur else None
                if not id_professeur or not Professeur.query.get(id_professeur):
                    flash('Professeur invalide.', 'error')
                    return redirect(url_for('cours.creer'))
            except (ValueError, TypeError):
                flash('Professeur invalide.', 'error')
                return redirect(url_for('cours.creer'))
            
            try:
                id_groupe = int(id_groupe) if id_groupe else None
                if not id_groupe or not Groupe.query.get(id_groupe):
                    flash('Groupe invalide.', 'error')
                    return redirect(url_for('cours.creer'))
            except (ValueError, TypeError):
                flash('Groupe invalide.', 'error')
                return redirect(url_for('cours.creer'))
            
            semestre_int = int(semestre) if semestre else None
            coefficient_float = float(coefficient) if coefficient else None
            
            # Génération automatique du code
            code_cours = generer_code_cours(nom_cours, type_cours, semestre_int)
            
            # Création du cours
            nouveau_cours = Cours(
                nom_cours=nom_cours,
                code_cours=code_cours,
                nombre_heures=nombre_heures,
                type_cours=type_cours,
                id_professeur=id_professeur,
                id_groupe=id_groupe,
                semestre=semestre_int,
                coefficient=coefficient_float
            )
            
            db.session.add(nouveau_cours)
            db.session.commit()
            
            # Notification des étudiants
            if request.form.get('notifier_etudiants') == 'on':
                from models import Etudiant, Notification
                etudiants = Etudiant.query.filter_by(id_groupe=id_groupe).all()
                notifications = []
                for etudiant in etudiants:
                    notifications.append(
                        Notification(
                            id_utilisateur=etudiant.id_etudiant,  # Assuming Etudiant extends/links to Utilisateur logic or similar ID space
                            # Note: In this system, Etudiant might need a linked Utilisateur account. 
                            # Checking init_db, Etudiant model does NOT inherit Utilisateur, but there are Utilisateur accounts with role 'etudiant'.
                            # Linking is usually done via email. Let's send to the User account associated with the student's email.
                            type_notification='modification',
                            message=f"📚 Nouveau cours : {nom_cours} ({type_cours})\n🔑 Code : {code_cours}\n📅 Semestre : {semestre_int or 'N/A'}"
                        )
                    )
                
                # Correction: We need to find the Utilisateur ID for the notifications table
                from models import Utilisateur
                emails = [e.email for e in etudiants]
                users = Utilisateur.query.filter(Utilisateur.email.in_(emails)).all()
                
                real_notifications = []
                for user in users:
                     real_notifications.append(
                        Notification(
                            id_utilisateur=user.id_utilisateur,
                            type_notification='modification',
                            message=f"📚 Nouveau cours : {nom_cours} ({type_cours})\n🔑 Code : {code_cours}\n📅 Semestre : {semestre_int or 'N/A'}"
                        )
                    )
                if real_notifications:
                    db.session.add_all(real_notifications)
                    db.session.commit()
                    flash(f'Cours créé et {len(real_notifications)} étudiants notifiés.', 'success')
                else:
                    flash(f'Cours créé (aucun étudiant notifié - comptes introuvables).', 'warning')
            else:
                flash(f'Cours "{nom_cours}" créé avec succès avec le code {code_cours}.', 'success')

            return redirect(url_for('cours.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du cours: {str(e)}', 'error')
            return redirect(url_for('cours.creer'))
    
    # GET: Afficher le formulaire
    try:
        professeurs = Professeur.query.filter_by(actif=True).order_by(Professeur.prenom, Professeur.nom).all()
        groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
    except (OperationalError, ProgrammingError):
        professeurs = []
        groupes = []
    
    return render_template('cours/creer.html', professeurs=professeurs, groupes=groupes)

@cours_bp.route('/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(id):
    """Modifier un cours (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent modifier des cours.', 'error')
        return redirect(url_for('cours.liste'))

    try:
        cours = Cours.query.get_or_404(id)
        
        if request.method == 'POST':
            nom_cours = request.form.get('nom_cours', '').strip()
            type_cours = request.form.get('type_cours', '')
            nombre_heures = request.form.get('nombre_heures')
            id_professeur = request.form.get('id_professeur')
            id_groupe = request.form.get('id_groupe')
            semestre = request.form.get('semestre')
            coefficient = request.form.get('coefficient')
            
            # Validation
            if not nom_cours:
                flash('Le nom du cours est requis.', 'error')
                return redirect(url_for('cours.modifier', id=id))
            
            try:
                nombre_heures = int(nombre_heures) if nombre_heures else 0
                if nombre_heures <= 0:
                    flash('Le nombre d\'heures doit être supérieur à 0.', 'error')
                    return redirect(url_for('cours.modifier', id=id))
            except (ValueError, TypeError):
                flash('Nombre d\'heures invalide.', 'error')
                return redirect(url_for('cours.modifier', id=id))
            
            semestre_int = int(semestre) if semestre else None
            coefficient_float = float(coefficient) if coefficient else None
            
            # Mise à jour
            cours.nom_cours = nom_cours
            cours.type_cours = type_cours
            cours.nombre_heures = nombre_heures
            cours.id_professeur = int(id_professeur)
            cours.id_groupe = int(id_groupe)
            cours.semestre = semestre_int
            cours.coefficient = coefficient_float
            
            db.session.commit()
            
            flash('Cours modifié avec succès.', 'success')
            return redirect(url_for('cours.liste'))
        
        # GET
        professeurs = Professeur.query.filter_by(actif=True).order_by(Professeur.prenom, Professeur.nom).all()
        groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
        return render_template('cours/modifier.html', cours=cours, professeurs=professeurs, groupes=groupes)
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la modification du cours: {str(e)}', 'error')
        return redirect(url_for('cours.liste'))

@cours_bp.route('/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    """Supprimer un cours"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('cours.liste'))
        
    try:
        cours = Cours.query.get_or_404(id)
        
        # Vérifier s'il y a des réservations
        from models import Reservation
        reservations_count = Reservation.query.filter_by(id_cours=id).count()
        
        if reservations_count > 0:
            flash(f'Impossible de supprimer ce cours car il a {reservations_count} réservations associées. Supprimez d\'abord les réservations.', 'error')
            return redirect(url_for('cours.liste'))
            
        db.session.delete(cours)
        db.session.commit()
        flash('Cours supprimé avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        
    return redirect(url_for('cours.liste'))

@cours_bp.route('/groupe/creer', methods=['GET', 'POST'])
@login_required
def creer_groupe():
    """Créer un nouveau groupe (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent créer des groupes.', 'error')
        return redirect(url_for('cours.liste'))
    
    if request.method == 'POST':
        try:
            nom_groupe = request.form.get('nom_groupe', '').strip()
            niveau = request.form.get('niveau', '').strip()
            filiere = request.form.get('filiere', '').strip()
            effectif = request.form.get('effectif')
            annee_academique = request.form.get('annee_academique', '').strip()
            
            # Validation
            if not nom_groupe:
                flash('Le nom du groupe est requis.', 'error')
                return redirect(url_for('cours.creer_groupe'))
            
            if not niveau:
                flash('Le niveau est requis.', 'error')
                return redirect(url_for('cours.creer_groupe'))
            
            try:
                effectif = int(effectif) if effectif else 0
                if effectif <= 0:
                    flash('L\'effectif doit être supérieur à 0.', 'error')
                    return redirect(url_for('cours.creer_groupe'))
            except (ValueError, TypeError):
                flash('Effectif invalide.', 'error')
                return redirect(url_for('cours.creer_groupe'))
            
            # Vérifier si le nom existe déjà
            if Groupe.query.filter_by(nom_groupe=nom_groupe).first():
                flash(f'Un groupe avec le nom "{nom_groupe}" existe déjà.', 'error')
                return redirect(url_for('cours.creer_groupe'))
            
            # Création du groupe
            nouveau_groupe = Groupe(
                nom_groupe=nom_groupe,
                niveau=niveau,
                filiere=filiere if filiere else None,
                effectif=effectif,
                annee_academique=annee_academique if annee_academique else None
            )
            
            db.session.add(nouveau_groupe)
            db.session.commit()
            
            flash(f'✅ Groupe "{nom_groupe}" créé avec succès ! Vous pouvez maintenant créer des cours pour ce groupe ou ajouter des étudiants.', 'success')
            return redirect(url_for('cours.liste_groupes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du groupe: {str(e)}', 'error')
            return redirect(url_for('cours.creer_groupe'))
    
    # GET: Afficher le formulaire
    return render_template('cours/creer_groupe.html')

@cours_bp.route('/groupes')
@login_required
def liste_groupes():
    """Liste des groupes (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent consulter la liste des groupes.', 'error')
        return redirect(url_for('cours.liste'))
    
    try:
        # Récupérer tous les groupes avec eager loading pour optimiser les requêtes
        groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
        
        # Charger les statistiques pour chaque groupe
        groupes_data = []
        for groupe in groupes:
            try:
                # Compter les étudiants et cours associés
                from models import Etudiant, Cours
                nombre_etudiants = Etudiant.query.filter_by(id_groupe=groupe.id_groupe).count()
                nombre_cours = Cours.query.filter_by(id_groupe=groupe.id_groupe).count()
                
                # Calculer le pourcentage de remplissage
                pourcentage_remplissage = (nombre_etudiants / groupe.effectif * 100) if groupe.effectif > 0 else 0
                
            except Exception:
                nombre_etudiants = 0
                nombre_cours = 0
                pourcentage_remplissage = 0
            
            groupes_data.append({
                'groupe': groupe,
                'nombre_etudiants': nombre_etudiants,
                'nombre_cours': nombre_cours,
                'pourcentage_remplissage': round(pourcentage_remplissage, 1)
            })
    except (OperationalError, ProgrammingError):
        groupes_data = []
    
    return render_template('cours/liste_groupes.html', groupes_data=groupes_data)

@cours_bp.route('/groupe/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_groupe(id):
    """Modifier un groupe (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('cours.liste_groupes'))
        
    try:
        groupe = Groupe.query.get_or_404(id)
        
        if request.method == 'POST':
            nom_groupe = request.form.get('nom_groupe', '').strip()
            niveau = request.form.get('niveau', '').strip()
            filiere = request.form.get('filiere', '').strip()
            effectif = request.form.get('effectif')
            annee_academique = request.form.get('annee_academique', '').strip()
            
            if not nom_groupe:
                flash('Le nom est requis', 'error')
                return render_template('cours/modifier_groupe.html', groupe=groupe)
                
            # Vérifier unicité si nom changé
            if nom_groupe != groupe.nom_groupe and Groupe.query.filter_by(nom_groupe=nom_groupe).first():
                flash('Un groupe avec ce nom existe déjà', 'error')
                return render_template('cours/modifier_groupe.html', groupe=groupe)
                
            groupe.nom_groupe = nom_groupe
            groupe.niveau = niveau
            groupe.filiere = filiere
            groupe.effectif = int(effectif) if effectif else 0
            groupe.annee_academique = annee_academique
            
            db.session.commit()
            flash('Groupe modifié avec succès', 'success')
            return redirect(url_for('cours.liste_groupes'))
            
        return render_template('cours/modifier_groupe.html', groupe=groupe)
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('cours.liste_groupes'))

@cours_bp.route('/groupe/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_groupe(id):
    """Supprimer un groupe"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('cours.liste_groupes'))
        
    try:
        groupe = Groupe.query.get_or_404(id)
        
        # Vérifications et suppression
        # (Pour simplifier, on suppose que les contraintes de clés étrangères géreront les erreurs ou on devrait vérifier manuellemnt)
        # Mais ici on va essayer de supprimer et catcher l'erreur d'intégrité
        db.session.delete(groupe)
        db.session.commit()
        flash('Groupe supprimé avec succès', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Impossible de supprimer ce groupe (il est probablement lié à des étudiants ou des cours).', 'error')
        
    return redirect(url_for('cours.liste_groupes'))

